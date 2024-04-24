import os, glob, sys, pdb
from datetime import datetime
from optparse import OptionParser

""" Config dictionnary. Key is name to be passed as command line argument. Value is array of processing steps in order.
Can sepecify either "cfg" : cmssw python config to be run using cmsRun, or "cmsDriver" : string of commands to be passed to cmsDriver.py
"""
multi_conf_dict = {
"HH_WWZZ_3l" : [
    { # LHE,GEN,SIM
      "release": "CMSSW_10_2_16_patch1", 
      "cmsDriver": 'cmsDriver.py Configuration/GenProduction/python/test_fragment_HH4V.py --python_filename HIG-RunIIFall18wmLHEGS-02890_3l_1_cfg.py --eventcontent RAWSIM,LHE  --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN-SIM,LHE --fileout file:HIG-RunIIFall18wmLHEGS-02890_3l.root --conditions 102X_upgrade2018_realistic_v11 --beamspot Realistic25ns13TeVEarly2018Collision --customise_commands process.RandomNumberGeneratorService.externalLHEProducer.initialSeed="int(24)" --step LHE,GEN,SIM --geometry DB:Extended --era Run2_2018  --no_exec  --mc ',
      "KeepOutput": False,
    },
    { # DIGI,DATAMIX,L1,DIGI2RAW
      "release": "CMSSW_10_2_5",
      "cmsDriver": 'cmsDriver.py --python_filename HIG-RunIIFall18wmLHEGS-02890_3l_2_cfg.py --eventcontent PREMIXRAW --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN-SIM-RAW --fileout file:HIG-RunIIAutumn18DRPremix-02460_3l_step1.root --pileup_input dbs:/Neutrino_E-10_gun/RunIISummer17PrePremix-PUAutumn18_102X_upgrade2018_realistic_v15-v1/GEN-SIM-DIGI-RAW --conditions 102X_upgrade2018_realistic_v15 --step DIGI,DATAMIX,L1,DIGI2RAW,HLT:@relval2018 --procModifiers premix_stage2 --nThreads 8 --geometry DB:Extended --filein file::HIG-RunIIFall18wmLHEGS-02890_3l.root --datamix PreMix --era Run2_2018 --no_exec --mc ',
      "KeepOutput": False,
    },

    { # RECO
      "release": "CMSSW_10_2_5",
      "cmsDriver": 'cmsDriver.py --filein file:HIG-RunIIAutumn18DRPremix-02460_3l_step1.root --fileout file:HIG-RunIIAutumn18DRPremix-02460.root --mc --eventcontent AODSIM --runUnscheduled --datatier AODSIM --conditions 102X_upgrade2018_realistic_v15 --step RAW2DIGI,L1Reco,RECO,RECOSIM,EI --procModifiers premix_stage2 --nThreads 8 --era Run2_2018 --python_filename HIG-RunIIFall18wmLHEGS-02890_3l_3_cfg.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring',
      "KeepOutput": False,
    },
    {  # MINIAOD
      "release": "CMSSW_10_2_5",
      "cmsDriver": 'cmsDriver.py --filein file:HIG-RunIIAutumn18DRPremix-02460.root --fileout file:HIG-RunIIAutumn18MiniAOD-02460.root --mc --eventcontent MINIAODSIM --runUnscheduled --datatier MINIAODSIM --conditions 102X_upgrade2018_realistic_v15 --step PAT --nThreads 8 --geometry DB:Extended --era Run2_2018 --python_filename HIG-RunIIFall18wmLHEGS-02890_3l_4_cfg.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring',
      "KeepOutput": True,
    },
    { # NANO
      "release": "CMSSW_10_2_22", #v7
      "cmsDriver": 'cmsDriver.py --filein file:HIG-RunIIAutumn18MiniAOD-02460.root --fileout file:HIG-RunIIAutumn18NanoAODv6-02285.root --mc --eventcontent NANOAODSIM --datatier NANOAODSIM --conditions 102X_upgrade2018_realistic_v20 --step NANO --nThreads 2 --era Run2_2018,run2_nanoAOD_102Xv1 --python_filename HIG-RunIIFall18wmLHEGS-02890_3l_5_cfg.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring',
      "KeepOutput": True,
    },
],


}

def findCmsswRelease(releaseName:str) -> str:
    """ Finds CMSSW release location (created with cmsrel). Returns path to src folder, ie  /grid_mnt/data__data.polcms/cms/cuisset/ZHbbtautau/cmsReleases/CMSSW_10_2_22/src/ """
    bases = ["/grid_mnt/data__data.polcms/cms/asculac/MCProduction/CMSSW_versions)"]
    for base in bases:
        pathToSrc = os.path.join(base, releaseName, "src")
        if os.path.isdir(pathToSrc):
            return pathToSrc
    raise RuntimeError("Could not find CMSSW release version " + releaseName)

# Script to submit MC production

if __name__ == "__main__" :

    parser = OptionParser()    
    parser.add_option("--base",      dest="base",      type=str,            default=None,                            help="Base output folder name")
    parser.add_option("--grid",      dest="grid",      type=str,            default=None,                            help="Gridpack location for step 0")
    parser.add_option("--process",   dest="process",   type=str,            default=None,                            help="Name of process ["+', '.join(multi_conf_dict.keys())+"]")
    parser.add_option("--maxEvents", dest="maxEvents", type=int,            default=50,                              help="Number of events per job")
    parser.add_option("--nJobs",     dest="nJobs",     type=int,            default=1,                               help="Number of jobs")
    parser.add_option("--start_from",dest="start_from",type=int,            default=0,                               help="Start random seed from")
    parser.add_option("--queue",     dest="queue",     type=str,            default='reserv',                        help="long or short queue")
    parser.add_option("--no_exec",   dest="no_exec",   action='store_true', default=False)
    parser.add_option("--resubmit",  dest="resubmit",  action='store_true', default=False)
    (options, args) = parser.parse_args()

    try:
        conf_dict = multi_conf_dict[options.process]
    except KeyError as e:
        print("Invalid process specified (" + str(e) + ")", file=sys.stderr)
        print("Possible options : " + ', '.join(multi_conf_dict.keys()))
        sys.exit(-5)
    
    outdir = options.base
    print(" ### INFO: Saving output in", outdir)
    os.system('mkdir -p '+outdir)

    if options.grid == None:
        sys.exit(" ### ERROR: Specify gridpack location")
    print(" ### INFO: Gridpack location is", options.grid)

    starting_index = int(options.start_from)
    ending_index = starting_index + int(options.nJobs)
    print(" ### INFO: Index range", starting_index, ending_index)
    os.system('mkdir -p '+outdir+'/jobs')

    status = {i: -1 for i in range(starting_index, ending_index)}

    for idx in range(starting_index, ending_index):
        
        resubmit = False

        os.system('mkdir -p '+outdir+'/jobs/' + str(idx))
        outJobName  = outdir + '/jobs/' + str(idx) + '/job_' + str(idx) + '.sh'
        # if options.resubmit: outJobName = outdir + '/jobs/' + str(idx) + '/job_' + str(idx) + '_re.sh'

        # random seed for MC production should every time we submit a new generation
        # it's obtained by summing current Y+M+D+H+M+S+job_number
        # now = datetime.now()
        # randseed = int(now.year) + int(now.month) + int(now.day) + int(now.hour) + int(now.minute) + int(now.second) + idx
        randseed = idx+1 # to be reproducible

        cmsRuns = []

        for step in range(len(conf_dict)):
            
            cur_dir = outdir + '/Step_' + str(step)
            os.system('mkdir -p '+cur_dir)
            outFileName = 'Step_' + str(step) + '_Ntuple_' + str(idx) + '.root' # filename in case of keeping the output on worker node
            outRootName = cur_dir + '/Ntuple_' + str(idx) + '.root'
            if step > 0:
                prev_dir = outdir + '/Step_' + str(step-1)
                inFileName = 'Step_' + str(step-1) +'_Ntuple_' + str(idx) + '.root' # filename in case input was kept on worker node
                inRootName = prev_dir + '/' + 'Ntuple_' + str(idx) + '.root'
            outLogName  = outdir + '/jobs/' + str(idx) + '/log_' + str(step) + '_' + str(idx) + '.txt'

            if options.resubmit:
                if not resubmit:
                  if os.path.isfile(outLogName):
                      if len(os.popen('tail '+outLogName+' | grep dropped').read()) > 0:
                          status[idx] = step
                          continue
                      elif len(os.popen('grep "Fatal" '+outLogName).read()) > 0 or len(os.popen('grep "fatal" '+outLogName).read()) > 0:
                          resubmit = True
                          if not "Error" in str(status[idx]):
                            status[idx] = "Error Step%s" %(str(step))
                  else:
                      continue # not started yet

            cfg = conf_dict[step].get('cfg', None)
            cmsDriverCommand = conf_dict[step].get('cmsDriver', None)
            assert (cfg is None) ^ (cmsDriverCommand is None), "In config, either cfg or cmsDriver must be set (not both)"
            release = conf_dict[step]['release']
            keep_previousStep = True if int(step) == 0 else conf_dict[int(step-1)]['KeepOutput']
            keep_currentStep = conf_dict[int(step)]['KeepOutput']

            scriptRun = 'cd "' + findCmsswRelease(release) + '"\n'
            scriptRun += 'cmsenv\n'
            scriptRun += 'eval `scram r -sh`\n'
            #scriptRun += 'cd %s\n' %(outdir + '/jobs/' + str(idx))
            scriptRun += 'cd -\n' # go back to job directory on node
            if cfg is not None: # cmsRun mode
              scriptRun += "cmsRun " + os.getcwd() + "/" + cfg + " outputFile=file:"+ (outRootName if keep_currentStep else outFileName) + \
                  " maxEvents="+str(options.maxEvents)+" randseed="+str(randseed)
              if step == 0: scriptRun = scriptRun+" inputFiles="+options.grid
              if int(step) > 0: 
                  scriptRun = scriptRun+" inputFiles=file:"+ (inRootName if keep_previousStep else inFileName)
              scriptRun += " >& "+outLogName + '\n'

            else: # cmsDriver mode
                scriptRun += cmsDriverCommand + f" --no_exec --python_filename Step_{step}_cfg.py -n {str(options.maxEvents)} "
                if int(step) > 0:
                  scriptRun += f"--filein 'file:{(inRootName if keep_previousStep else inFileName)}' "
                scriptRun += f"--fileout 'file:{(outRootName if keep_currentStep else outFileName)}' "
                
                scriptRun += "\n"
                scriptRun += f"echo 'process.RandomNumberGeneratorService.generator.initialSeed = {str(randseed)}' >> Step_{step}_cfg.py\n"
                if step == 0:
                  scriptRun += f"echo 'process.RandomNumberGeneratorService.externalLHEProducer.initialSeed = {str(randseed)}' >> Step_{step}_cfg.py\n"
                  scriptRun += f"echo 'process.externalLHEProducer.args = cms.vstring(\"{options.grid}\")' >> Step_{step}_cfg.py\n"
                  scriptRun += f"echo 'process.externalLHEProducer.nEvents = cms.untracked.uint32({options.maxEvents})' >> Step_{step}_cfg.py\n"
                scriptRun += f"cmsRun -n 8 Step_{step}_cfg.py  >&{outLogName}\n"

            
            if int(step) > 0 and not keep_previousStep:
                scriptRun += "rm "+inFileName + '\n'
                if int(step) == 1: # remove LHE file as well (otherwise it gets shipped back at the end of the job)
                    scriptRun += f"rm Step_0_Ntuple_{str(idx)}_inLHE.root\n"
            cmsRuns.append(scriptRun)

        if not options.resubmit:
            skimjob = open (outJobName, 'w')
            skimjob.write ('#!/bin/bash\n')
            skimjob.write ('set -e\n') # abort script at first error
            skimjob.write ('export X509_USER_PROXY=~/.t3/proxy.cert\n')
            skimjob.write ('source /cvmfs/cms.cern.ch/cmsset_default.sh\n')
            for cmsRun in cmsRuns:
                skimjob.write(cmsRun)
            skimjob.close ()

            os.system ('chmod u+rwx ' + outJobName)
        
        if options.resubmit:
            if not resubmit: continue
            if not options.no_exec: os.system ('rm ' + outdir + '/jobs/' + str(idx) + '/log_*')

        # command = ('/home/llr/cms/evernazza/t3submit -'+options.queue+' \'' + outJobName +"\'")
        command = ('/opt/exp_soft/cms/t3/t3submit -8c -'+options.queue+' \'' + outJobName +"\'")
        print(command)
        if not options.no_exec: os.system (command)

    if options.resubmit:
        # pdb.set_trace()
        done = [i for i in status.keys() if status[i] == 6]
        if len(done) == int(options.nJobs):
            print(" ### CONGRATULATION! EVERYTHING IS DONE! :)\n")
        else:
            error = [i for i in status.keys() if "Error" in str(status[i])]
            print(" ### JOBS RESUBMITTED: {}\n".format(error))
            running_0 = [i for i in status.keys() if status[i] == -1]
            running_1 = [i for i in status.keys() if status[i] == 0]
            running_2 = [i for i in status.keys() if status[i] == 1]
            running_3 = [i for i in status.keys() if status[i] == 2]
            running_4 = [i for i in status.keys() if status[i] == 3]
            running_5 = [i for i in status.keys() if status[i] == 4]
            running_6 = [i for i in status.keys() if status[i] == 5]
            print(" ### INFO: Running Step 0", running_0)
            print(" ### INFO: Running Step 1", running_1)
            print(" ### INFO: Running Step 2", running_2)
            print(" ### INFO: Running Step 3", running_3)
            print(" ### INFO: Running Step 4", running_4)
            print(" ### INFO: Running Step 5", running_5)
            print(" ### INFO: Running Step 6", running_6)
            print(" ### INFO: Done", done)
