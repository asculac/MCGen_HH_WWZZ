# Monte Carlo generator for HH_WWZZ

This is a private MC sample generator for HH->WWZZ analysis aiming specific lepton multiplicity (3l,4l and 5l) based on [XZZbbTauTau manual](https://github.com/elenavernazza/MCGeneration_XZZbbtautau/tree/main)
## Gridpacks

We are using existing gridpack from the original HH-> 4V sample ([GluGluToHHTo4V_node_cHHH1](https://cmsweb.cern.ch/das/request?input=dataset%3D%2FGluGluToHHTo4V_node_cHHH1_TuneCP5_PSWeights_13TeV-powheg-pythia8%2FRunIIAutumn18NanoAODv7-Nano02Apr2020_102X_upgrade2018_realistic_v21-v1%2FNANOAODSIM&instance=prod/global)) generated for multilepton analysis. The gridpack can be found from fragments available in McM. In our case the fragment can be seen [here](https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/requests/get_fragment/HIG-RunIIFall18wmLHEGS-02890/0) and the corresponding gridpack is found in the args option:


```bash
args = cms.vstring('/cvmfs/cms.cern.ch/phys_generator/gridpacks/slc6_amd64_gcc700/13TeV/powheg/V2/ggHH_EWChL_NNPDF31_13TeV_M125_cHHH1/v3/ggHH_EWChL_slc6_amd64_gcc700_CMSSW_10_2_5_patch1_my_ggHH_EWChL.tgz')
```

## Fragments

Since we are aiming to produce exact lepton multiplicity, we have to alter the original fragment, mainly the processParameters. We want to have only HH->WWZZ, W->lv or W->qq, Z->ll or Z->qq and in the end we are targeting specific lepton multiplicity (3l,4l,5l). Check the line comments to understand the purpose of each line.
```python
processParameters = cms.vstring(
            'POWHEG:nFinal = 2',   ## Number of final state particles
            '23:mMin = 0.05',
            '24:mMin = 0.05',
            '25:m0 = 125.0',
            '25:onMode = off',
            '25:onIfMatch = 24 -24', #H->w+w-
            '25:onIfMatch = 23 23', #H->ZZ
            '23:onMode = off', # disable all Z decay modes
            '23:onIfAny = 1 2 3 4 5 6 7 8 11 13 15', # enable only Z->ll and Z->qq
            'ResonanceDecayFilter:filter = on',
            'ResonanceDecayFilter:exclusive = on', #off: require at least the specified number of daughters, on: require exactly the specified number of daughters
            'ResonanceDecayFilter:mothers = 25,24,23', #which mothers will be considered for later specified daughers
            # 'ResonanceDecayFilter:wzAsEquivalent = on',
            'ResonanceDecayFilter:eMuAsEquivalent = on', #treat electrons and muons as equivalent
            'ResonanceDecayFilter:daughters = 24,24,23,23,11,11,11',
          ), #asking to have only WWZZ with exactly 3l (l=e,mu)
```

After altering the fragment we are ready to make the setup for the production.

## Production
### Before running the steps
One first needs to understand the CMSSW version used per each step of production (usually the steps are LHE,GEN,SIM-RECO-MINIAOD-NANOAOD). You can find the CMSSW version in the JSON tab available in the [ReqMgr](https://cmsweb.cern.ch/reqmgr2/fetch?rid=cmsunified_ACDC0_task_HIG-RunIIFall18wmLHEGS-02890__v1_T_200325_143424_7510). In the same page you can find the options used to produce that sample if tou open configFiles from the "Config Cache List" and check the
``` python
# with command line options:
```

For our example, first step is given in [Task1: HIG-RunIIFall18wmLHEGS-02890_0: ConfigCacheID..](Task1: HIG-RunIIFall18wmLHEGS-02890_0: ConfigCacheID) and is
``` python
# with command line options: Configuration/GenProduction/python/HIG-RunIIFall18wmLHEGS-02890-fragment.py --fileout file:HIG-RunIIFall18wmLHEGS-02890.root --mc --eventcontent RAWSIM,LHE --datatier GEN-SIM,LHE --conditions 102X_upgrade2018_realistic_v11 --beamspot Realistic25ns13TeVEarly2018Collision --step LHE,GEN,SIM --geometry DB:Extended --era Run2_2018 --python_filename /afs/cern.ch/cms/PPD/PdmV/work/McM/submit/HIG-RunIIFall18wmLHEGS-02890/HIG-RunIIFall18wmLHEGS-02890_1_cfg.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring --customise_commands process.RandomNumberGeneratorService.externalLHEProducer.initialSeed=int(24) -n 57
```
Locally, you can alter this command and test it. First you need to have the right CMSSW version (check JSON). In this case it is
``` bash
cmsrel CMSSW_10_2_17  #should be CMSSW_10_2_16_patch1 but it is not available
```
Then "install" your fragment in the CMSSW environment. 
``` bash
cd CMSSW_X_Y_Z/src/
cmsenv
mkdir -p Configuration/GenProduction/python/
touch Configuration/GenProduction/python/<my_fragment>.py
```
This fragment should be the altered one from the previous steps. To "install" it, just run:
``` bash
scram b
```
Now you are ready to run STEP 0.
### STEP 0
Simply do:
``` bash
cmsDriver.py Configuration/GenProduction/python/test_fragment_HH4V.py --fileout file:HIG-RunIIFall18wmLHEGS-02890_3l.root --mc --eventcontent RAWSIM,LHE --datatier GEN-SIM,LHE --conditions 102X_upgrade2018_realistic_v11 --beamspot Realistic25ns13TeVEarly2018Collision --step LHE,GEN,SIM --geometry DB:Extended --era Run2_2018 --python_filename HIG-RunIIFall18wmLHEGS-02890_1_3l_Step0_cfg.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring -n 10
```
``` bash
cmsRun HIG-RunIIFall18wmLHEGS-02890_1_3l_Step0_cfg.py
```
This will use my test_fragment_HH4V.py (produced and installed in CMSSW in previous steps) and generate RAWSIM&LHE root files which will later be used in next step.

