import acsys.dpm
import datetime
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np

datetype=0  #0 for interval, 1 for specified range

if datetype==0:
    dur=int(1*86400) #duration in seconds, 86400 sec in day
    #dur=3600*6 #duration in seconds, 86400 sec in day
    xstr='Plot end time of ' + datetime.datetime.strftime(datetime.datetime.now(), '%d-%b-%Y %H:%M:%S')
elif datetype==1:
    starttime=datetime.datetime(2024, 8, 22, 0, 0, 0)  #year, month, day, hour, min, sec - no leading zeroes
    endtime=datetime.datetime(2024, 8, 23, 0, 0, 0)
    xstr='Plot end time of ' + datetime.datetime.strftime(endtime, '%d-%b-%Y %H:%M:%S')

vacparams={"T:VEBCG": "DS BL (VEBCG)",
#    "T:VEBPG": "DS BL (VEBPG)"
#    "T:VFBCG": "US BL (VFBCG)",
    "T:VCCG": "Coupler (VCCG)",
    "T:VEICCG": "DS Ins (VEICCG)",
    "T:VFICCG": "US Ins (VFICCG)",
#    "T:VFIPG": "US Ins PG (VFIPG)",
#    "T:VEIPG": "DS Ins PG (VEIPG)",
#    "T:VEIRCG": "DS RIns (VEIRCG)",
#    "T:VFIRCG": "US RIns (VFIRCG)",
#    "T:VEBIPP": "DS BL IPP (VEBIPP)",
#    "T:VFBIPP": "US BL IPP (VFBIPP)",
#    "T:VCIPP": "CP IPP (VCIPP)"
    }

tempparams={#"t:1ct114": "Cav 1",
    "t:5ct114": "Cav 5",
    "t:ct402": "Magnet",
    "t:ct512": "Shield",
#    "t:cpt602": "Cav Jacket Press"
#    "T|VPMTOK": "Vacuum Permit",
#    "t:7ct118": "Cav7COM118",
#    "t:7ct120": "Cav7HOM120",
#   "t:ct501": "Line A Temp",
#    "T:2CT118": "Cav 2 HOM"
    }

async def plot(con):
    # Add acquisition requests
    if plottype=='vac':
        params=vacparams
    elif plottype=='temp':
        params=tempparams
        
    for entry in params:
        # Setup context
        async with acsys.dpm.DPMContext(con) as dpm:
            print("Gathering data for", entry)
            data=[]
            times=[]
            if datetype==0:
                entrystr=entry+'@P,1000,true<-LOGGERDURATION:'+str(dur*1000)
                await dpm.add_entry(0,entrystr)
            elif datetype==1:
                entrystr=entry+'@P,1000,true<-LOGGER:'+str(int(round(starttime.timestamp()*1000)))+':'+str(int(round(endtime.timestamp()*1000)))
                #print(entrystr)
                await dpm.add_entry(0,entrystr)
            # Start acquisition
            await dpm.start()
    
            # Process incoming data
            async for evt_res in dpm:
                if evt_res.isReadingFor(0):
                    # Exit condition: empty data means we're done
                    if evt_res.data == []:
                        break
                    else:  
                        data.extend(evt_res.data)
                        for i in evt_res.micros:
                            times.append(datetime.datetime.fromtimestamp(i/1000000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-5])

                else:
                    print(f'Status response: {evt_res}')
            #add plot entry for this parameter
            #print (times, data)
            
            # Handle any parameter scaling here, quick ugly hack @fix
            if entry=='T|VPMTOK':
                plt.plot(np.array(times, dtype='datetime64[ms]'), np.array(data)/200, label=params[entry])
            else:
                plt.plot(np.array(times, dtype='datetime64[ms]'), data, label=params[entry])

gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1]) 
plt.figure(figsize=[12,8], dpi=100)
ax1 = plt.subplot(gs[0])
plt.style.use('seaborn-v0_8-notebook')
plt.yscale('log')
plt.ylabel('Pressure [torr]')
plt.ylim([float(1E-10),float(1E-3)])
plt.setp(ax1.get_xticklabels(), visible=False)
plt.grid()

plottype='vac'
acsys.run_client(plot)

plt.legend()

ax2 = plt.subplot(gs[1], sharex=ax1)
plt.ylabel('Temp [K]')

plt.xlabel(xstr)
plt.grid()

plottype='temp'
acsys.run_client(plot)

plt.legend()
plt.show()