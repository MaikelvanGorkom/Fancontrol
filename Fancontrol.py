import paramiko
import pandas as pd

maxtemp = 65			# Maximum temperature, when above change fan speed
rangetemp = 5 			# degrees below maxtemp there will be no changes

fanpercstepdown = 1		#Step down is fan slower (less noisie), temp up
fanpercstepup = 3		#step up is fan harder (more noisie), temp down


percandbyte = pd.DataFrame({
	'perc':[
		'_1%','_2%','_3%','_4%','_5%','_6%','_7%','_8%','_9%','_10%',
		'_11%','_12%','_13%','_14%','_15%','_16%','_17%','_18%','_19%','_20%',
		'_21%','_22%','_23%','_24%','_25%','_26%','_27%','_28%','_29%','_30%',
		'_31%','_32%','_33%','_34%','_35%','_36%','_37%','_38%','_39%','_40%',
		'_41%','_42%','_43%','_44%','_45%','_46%','_47%','_48%','_49%','_50%',
		'_51%','_52%','_53%','_54%','_55%','_56%','_57%','_58%','_59%','_60%',
		'_61%','_62%','_63%','_64%','_65%','_66%','_67%','_68%','_69%','_70%',
		'_71%','_72%','_73%','_74%','_75%','_76%','_77%','_78%','_79%','_80%',
		'_81%','_82%','_83%','_84%','_85%','_86%','_87%','_88%','_89%','_90%',
		'_91%','_92%','_93%','_94%','_95%','_96%','_97%','_98%','_99%','_100%'],
	'byte':[
		'2','5','7','10','12','15','17','20','22','25',
		'27','30','32','35','37','40','42','45','48','51',
		'52','55','57','60','62','65','67','70','73','76',
		'78','80','82','85','87','90','93','96','99','102',
		'104','106','108','111','114','117','120','122','124','127',
		'130','132','134','137','140','143','146','148','150','153',
		'155','157','160','163','166','169','171','174','177','179',
		'181','183','185','187','190','193','196','199','202','205',
		'207','209','211','213','216','219','222','224','227','230',
		'232','234','236','238','241','244','247','249','252','255',
		]
})



def fanprocstatus(fannumber):
	fanperc = 'show system1/fan' + str(fannumber + 1)
	client = paramiko.client.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(sshilohost, username=sshilouser, password=sshilopass)
	_stdin, _stdout,_stderr = client.exec_command(fanperc)
	completefaninfo = (_stdout.read().decode()).split("\n")
	for line in completefaninfo:
		if "DesiredSpeed" in line:
			splitline = ((line.split("="))[1].split(" "))[0]
	client.close()
	return splitline

sshilohost = '192.168.178.80'
sshilouser = 'administrator'
sshilopass = 'ModenaOrangeHulkHo\'ed1'

sshtemphost = 'proxmox1'
sshtempuser = 'root'
sshtemppass = 'ModenaOrangeHulkHo\'ed1'

tempzones = ['zone1','zone2']
temps = []

tuneddown = 'NO'

## Get status of fans
fans = [0,1,2,3]
fanscurrentperc = []
for fan in fans: 
	#adjustfanspeed = 'fan p '+str(fan)+ ' max '+str(maxfanspeed)
	client = paramiko.client.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(sshilohost, username=sshilouser, password=sshilopass)
	fanproc = fanprocstatus(fan)
	fanscurrentperc.append(fanproc)
	client.close() 
fanhighestperc = max(fanscurrentperc)

currentperc = "_"+fanhighestperc+"%"
currentbyte = percandbyte.loc[percandbyte['perc'].str.contains(currentperc)]
currentbyte = currentbyte.values[0][1]

stepupperc = "_"+str(int(fanhighestperc)+fanpercstepup) +"%"
stepupbyte = percandbyte.loc[percandbyte['perc'].str.contains(stepupperc)]
stepupbyte = stepupbyte.values[0][1]

stepdownperc = "_"+str(int(fanhighestperc)-fanpercstepdown) +"%"
stepdownbyte = percandbyte.loc[percandbyte['perc'].str.contains(stepdownperc)]
stepdownbyte = stepdownbyte.values[0][1]

for tempzone in tempzones:
	checkzone = 'cat /sys/class/thermal/thermal_'+tempzone+'/temp'
	client = paramiko.client.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(sshtemphost, username=sshtempuser, password=sshtemppass)
	_stdin, _stdout,_stderr = client.exec_command(checkzone)
	temp = _stdout.read().decode()
	temps.append(int(temp))
	client.close()

#avgtemp = (temps/len(tempzones))/1000
maxtempzone = max(temps)/1000
print("Current temperature: "+str(maxtempzone))
print("Current fan CPU:     "+str(fanhighestperc))
print("Current byte set:    "+str(currentbyte))
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

# If the temperature is above max temp, start cooling
if maxtempzone > maxtemp:
	for fan in fans: 
		adjustfanspeed = 'fan p '+str(fan)+ ' max '+ stepupbyte
		client = paramiko.client.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(sshilohost, username=sshilouser, password=sshilopass)
		_stdin, _stdout,_stderr = client.exec_command(adjustfanspeed)
		client.close()
	
	print("New fanspeed : "+ stepupbyte +" of 255 / "+str(int(fanhighestperc)+fanpercstepup)+"%" )
	#stepupbyte

if maxtempzone <= maxtemp:
	if maxtempzone < (maxtemp - rangetemp):
		for fan in fans: 
			adjustfanspeed = 'fan p '+str(fan)+ ' max '+ stepdownbyte
			client = paramiko.client.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(sshilohost, username=sshilouser, password=sshilopass)
			_stdin, _stdout,_stderr = client.exec_command(adjustfanspeed)
			client.close()
		print("New fanspeed : "+ stepdownbyte +" of 255 / "+str(int(fanhighestperc)-fanpercstepdown)+"%" )
