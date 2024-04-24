#!/usr/bin/env python

import ROOT
import array
import sys

ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kError;")

class GenPart:
  def __init__(self, pt, eta, phi, mass, status, statusFlags, genPartIdxMother, pdgId, idx):
    self.pt = pt
    self.eta = eta
    self.phi = phi
    self.mass = mass
    self.status = status
    self.statusFlags = statusFlags
    self.genPartIdxMother = genPartIdxMother
    self.pdgId = pdgId
    self.idx = idx

# Function for finding daughter particles
def find_daughters(parent, collection):
  daughters = []
  for particle in collection:
    if particle.genPartIdxMother == parent.idx:
      daughters.append(particle)

  daughters_id = [ daughter for daughter in daughters if daughter.pdgId == parent.pdgId ]
  if daughters_id:
    assert(len(daughters_id) == 1)
    # If one of the descendants is the particle itself, repeat the search
    daughters = find_daughters(daughters_id[0], collection)
  return daughters

# Configurable parameters
MAX_INSTANCES = 4000
IS_LAST_COPY = (1 << 13)

# Define arrays to store the data
nGenPart = array.array('I', [0])
GenPart_pt = array.array('f', [0.0] * MAX_INSTANCES)
GenPart_eta = array.array('f', [0.0] * MAX_INSTANCES)
GenPart_phi = array.array('f', [0.0] * MAX_INSTANCES)
GenPart_mass = array.array('f', [0.0] * MAX_INSTANCES)
GenPart_status = array.array('i', [0] * MAX_INSTANCES)
GenPart_statusFlags = array.array('i', [0] * MAX_INSTANCES)
GenPart_genPartIdxMother = array.array('i', [0] * MAX_INSTANCES)
GenPart_pdgId = array.array('i', [0] * MAX_INSTANCES)

# Open the ROOT file
fn = sys.argv[1]
fp = ROOT.TFile.Open(fn, 'read')

# Get the TTree
tree = fp.Get("Events")

# Set branch addresses
tree.SetBranchAddress("nGenPart", nGenPart)
tree.SetBranchAddress("GenPart_pt", GenPart_pt)
tree.SetBranchAddress("GenPart_eta", GenPart_eta)
tree.SetBranchAddress("GenPart_phi", GenPart_phi)
tree.SetBranchAddress("GenPart_mass", GenPart_mass)
tree.SetBranchAddress("GenPart_status", GenPart_status)
tree.SetBranchAddress("GenPart_statusFlags", GenPart_statusFlags)
tree.SetBranchAddress("GenPart_genPartIdxMother", GenPart_genPartIdxMother)
tree.SetBranchAddress("GenPart_pdgId", GenPart_pdgId)

tree.SetBranchStatus("*", 0)
tree.SetBranchStatus("*GenPart*", 1)

# Loop over the events
nof_entries = tree.GetEntries()
counter = {}

for idx in range(nof_entries):
  tree.GetEntry(idx)

  # Populate the GenPart collection
  genParts = []
  for i in range(nGenPart[0]):
    genParts.append(GenPart(
      GenPart_pt[i], GenPart_eta[i], GenPart_phi[i], GenPart_mass[i],
      GenPart_status[i], GenPart_statusFlags[i], GenPart_genPartIdxMother[i],
      GenPart_pdgId[i], i
    ))

  # Find the Higgs pair
  genHiggses = []
  for genPart in genParts:
    if genPart.pdgId == 25 and genPart.statusFlags & IS_LAST_COPY:
      genHiggses.append(genPart)
  assert(len(genHiggses) == 2)

  # Find Higgs daughters
  label = ''
  nof_leptons, nof_quarks, nof_neutrinos, nof_tau = 0, 0, 0, 0
  for genHiggs in genHiggses:
    higgsDaughters = find_daughters(genHiggs, genParts)
    assert(len(higgsDaughters) == 2)
    for higgsDaughter in higgsDaughters:
      if abs(higgsDaughter.pdgId) == 23:
        label += 'Z'
      elif abs(higgsDaughter.pdgId) == 24:
        label += 'W'
      elif abs(higgsDaughter.pdgId) == 15:
        label += 't'
      else:
        print("Invalid Higgs daughter found: {}".format(higgsDaughter.pdgId))

      if abs(higgsDaughter.pdgId) == 15:
        # No point in checking the descendants of the tau lepton
        continue

      higgsGrandDaughters = find_daughters(higgsDaughter, genParts)
      assert(len(higgsGrandDaughters) == 2)
      for higgsGrandDaughter in higgsGrandDaughters:

        # Count the number of charged leptons, quarks and neutrinos
        if abs(higgsGrandDaughter.pdgId) in [ 11, 13 ]:
          nof_leptons += 1
        elif abs(higgsGrandDaughter.pdgId) in [ 15 ]:
          nof_tau += 1
        elif abs(higgsGrandDaughter.pdgId) in [ 1, 2, 3, 4, 5 ]:
          nof_quarks += 1
        elif abs(higgsGrandDaughter.pdgId) in [ 12, 14, 16 ]:
          nof_neutrinos += 1
        # else:
        #   print("Invalid Higgs granddaughter found: {}".format(higgsGrandDaughter.pdgId))

  label = ''.join(sorted(label))
  label+= ":{} L {} Q {} Nu {} Tau".format(nof_leptons,nof_quarks,nof_neutrinos, nof_tau)
#   label += f':{nof_leptons}L{nof_quarks}Q{nof_neutrinos}Nu'
  if label not in counter:
    counter[label] = 0
  counter[label] += 1

# Close the file
fp.Close()

print("Processed {} event(s) from file {}".format(nof_entries,fn))
for entry in sorted(counter.items(), key = lambda x: x[1], reverse = True):
#   print(f'  {entry[0]} -> {entry[1]} ({entry[1] / nof_entries * 100:.2f}%)')
  print( "{} -> {} ({}%)".format(entry[0],entry[1],entry[1] / nof_entries * 100) )