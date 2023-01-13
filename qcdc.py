#!/usr/bin/env python3
#element list implementation for $atoms
from molmass import Formula
import pandas as pd
import os
import numpy as np
#import math
import re

###VARIABLE DEFINITIONS###
from scipy.constants.constants import h, k, c, N_A, R, pi, milli
from scipy.constants import physical_constants
TEMPERATURE = 298.15 #K
PRESSURE = 1e5   #Pa
QRRHO_CUTOFF = 100 #cm-1
MOLES = 1 #mol
MOMI = 'MomentOfInertia (amu/bohr^2)'
M_MASS = 'molecular mass [g/mol]'
#BOHR2ANGSTROM = physical_constants['Bohr radius'][0]/1e-10

#physical constants
a0 = physical_constants['Bohr radius'][0]
amu = physical_constants['atomic mass constant'][0]
EH2KJMOL=2625.5002
#we did not implement anything with symmetry. linear molecules may be problematic, 
#do not expect correct free energies for symmetric molecules
SIGMA = 1

###LOGGING###
#Apparently not needed right anymore
#import logging
#fname = 'logging.log'
#logging.basicConfig(
#    filename=fname,
#    filemode="w",
#    format='%(asctime)s %(message)s',
#    datefmt='%m/%d/%Y %I:%M:%S %p',
#    level=logging.DEBUG
#    )

def main (infile='tree.dat'):
    #df gets converted to dataframe later
    df = []

    for root, dirs, files in os.walk(os.path.curdir):
        try:

            #ser reflects one series, although we use dict to be faster
            ser = dict()

            #This is sometimes useful for data evaluation purposes
            ser['Folder'] = root.split(os.sep)[-1] #name of folder only
            ser['Group'] = root.strip(str(ser['Folder'])) #name of root without folder
            ser['Root'] = root

            #TURBOMOLE functions
            #the function changes ser by saving information from 'control'
            get_control2(ser, root, files)

            #gets last saved [0]: total energy [1]:kinetic energy, [2]:potential energy
            filename = 'energy'
            if filename in files:
                ser['SPE'] = get_energy2(root)[0]*EH2KJMOL 
            

            #read coordinate information and calculate moments of inertia
            filename = 'coord'
            if filename in files: #we assume turbomole format
                #get coords in angstrom and elementsymbols
                xyz, elem = get_coord3(root) #bohr
    
                #We need mass information of the elements
                elem_masses = mass_of_elements(elem) #g/mol
                ser[M_MASS] = np.sum(elem_masses)
    
                #When we calculate moments of inertia, we need centralized coordinates
                xyz_central = xyz - center_of_mass(xyz, elem_masses)
                ser[MOMI] = {
                        'xx': moment_of_inertia(xyz_central, elem_masses, 1, 2),
                        'yy': moment_of_inertia(xyz_central, elem_masses, 0, 2),
                        'zz': moment_of_inertia(xyz_central, elem_masses, 0, 1)
                        }
                momi = [ser[MOMI]['xx'],ser[MOMI]['yy'],ser[MOMI]['zz']]
                #print(momi)
                #get_coord (ser, root, dat='last-geo.xyz') 
                #print(ser[inerta], ser[inertb], ser[inertc])
    
            #gets frequencies from vibspectrum and calculates RRHO thermal corrections and quasi-RRHO Gibbs free energy
            filename = 'vibspectrum'
            if filename in files:
                tmp = get_vibspectrum (root)
                ser['Vibspectrum'] = dict(tmp)
                freqs = np.asarray(tmp)[:,1]
                #print(freqs)
                ser['ThermalCorrections'] = calculate_gibbs(freqs, momi, ser[M_MASS])
                positive_freqs = np.abs(freqs)
            #do this for transition states, frequencies start to count from 1!
                if ser['Vibspectrum'][1] < 0.:
                    ser['ThermalCorrections (sign inverted)'] = calculate_gibbs(positive_freqs, momi, ser[M_MASS])
                    ts_freqs = positive_freqs
                    ts_freqs[0] = -ts_freqs[0]
                    ser['ThermalCorrections (sign inverted) for TS'] = calculate_gibbs(ts_freqs, momi, ser[M_MASS])
                else:
                    #In case, all frequencies are positive, we just use copy the old results, such that it is easier to use later.
                    #However, this is not a deep copy. A deep copy should not be necessary.
                    ser['ThermalCorrections (sign inverted)'] = ser['ThermalCorrections'].copy() 
    
    
            #gets information on HOMO and LUMO (energy and orbital number)
            filename = 'eiger.out'
            if filename in files:
                get_eiger (ser, root) 
    
            #gets cosmors values, filename has to be out.tab
            filename = 'out.tab'
            if filename in files:
                get_cosmors(ser, root, dat='out.tab')
            df.append(ser)
        except IndexError as e:
            print(f"{e}! look at {root}/{filename}. Please rename or delete the file, directory is skipped")
    df = pd.DataFrame(df)
    #df.to_csv('data.csv',index=False)
    df.to_json('data.json')
    print(df)
    print(df.info())

def get_control2(ser, root, files):#dat='control'):
    """scans the text and produces tokens from $ to $ character of control
    tokens are then parsed by a certain
    the control file is essential to turbomole
    """
    if 'control' in files:
        with open(root+os.sep+'control') as file:
            string = file.read()
            #Use format of control file to get easily parsable multiline strings
            x = string.split('$')
            for token in x:
                if token.startswith('cosmo\n'):  
                    ser['Cosmo'] = dict(re.findall(equality_re, token))
                    #print(ser['Cosmo'])
                elif token.startswith('rundimensions'):
                    ser['RunDimensions'] = dict(re.findall(equality_re, token))
                elif token.startswith('forceupdate'):
                    ser['ForceUpdate'] = dict(re.findall(equality_re, token))
                elif token.startswith('scfdamp '):
                    ser['SCFDamp'] = dict(re.findall(equality_re, token))
                elif token.startswith('fermi'):
                    ser['Fermi'] = dict(re.findall(equality_re, token))
                    #print(ser['Fermi'])
                elif token.startswith('scfconv '):
                    ser['SCFConv'] = int(token.split()[1])
                elif token.startswith('rij'):
                    ser['RI'] = True
                elif token.startswith('dft'):
                    #TODO compile explicit regexes and use them instead
                    ser['DFT'] = right_words(['functional','gridsize'], token)  
                #if Basis is the same for all elements save single Basis Set and remove Basis for elements
                elif token.startswith('atoms'):
                    ser['BasisForElement'] = dict(re.findall(equality_basis_re, token))
                    ser['BasisSet'] = set(ser['BasisForElement'].values())
                    #I kick it out again because its unusual 
                    if len(ser['BasisSet']) == 1: 
                        ser['BasisForElement'] = None 
                elif token.startswith('disp'):
                    ser['Dispersion'] = token.strip('\n')
                elif token.startswith('ssquare'):
                    ser['S^2'] = float(token.split()[3])
            #greedily finds all file= expressions and saves them together with previous keyword
            ser['filenames'] = dict(re.findall(r'\$(\S*)\s[^$]*?\sfile=(\S*)',string,re.DOTALL))  

equality_re = re.compile(r"(\S+)\s*=\s*(\S+)")
equality_basis_re = re.compile(r"=([a-z]{1,2})\s(\S+)")
fileequal_re = re.compile(r".*file=\s*(\S+)")

def right_word(substring, string):
    """returns right word of substring until end of line is reached..?"""
    return (re.search("[\n\r][ \t]*"+substring+"[ \t]*([^\n\r]*)", string))
def right_words(substringlist, string):
    """returns right word of substring for a list of substrings"""
    return dict((substring, re.search(substring+"[ \t]*([^\n\r]*)", string)[1]) for substring in substringlist)
    #print(dict((substring, re.search(substring+"[ \t]*([^\n\r]*)", string)[1]) for substring in substringlist))

#[ a]+[-+]?\d*\.*\d+")#add this to obtain IR intensities eventually
RE_VIBSPECTRUM = re.compile(r"([-+]?\d*\.*\d+)[ a]+([-+]?\d*\.*\d+)")
def get_vibspectrum(root):
        """
        extract information (frequencies) from 'vibspectrum'
        ser : dictionary
        root : path to file
        """
        with open(root+os.sep+'vibspectrum') as file:
            return [(int(i), float(j)) for i, j in re.findall(RE_VIBSPECTRUM, file.read())]
            #return re.findall(RE_VIBSPECTRUM, file.read())


def calculate_gibbs(freqs, momi, mass, temp=TEMPERATURE, press=PRESSURE, sig=SIGMA, cutoff=QRRHO_CUTOFF):
    """
    saver : dict for saving information
    freqs : np array containing frequencies
    momi : array with moments of inertia
    temperature, pressure, sigma : these parameters are defined by default values 
    and saved in the dictionary but stay flexible through being arguments of the function

    We use different versions to approximate Gibbs free energy:

    """
    saver = dict()
    freqs = np.asarray(freqs)
    positive_freqs = freqs[np.where(freqs > 0.)]
    #shift this into calc_grimme_short
    low_positive_freqs = positive_freqs[np.where(positive_freqs < cutoff)]

    #calculate RRHO chemical potential at standard conditions
    (saver['qtrans'], saver['qvib'], saver['qrot'], saver['zpe'], saver['chempot']) = calc_partition_c(
            freqs, momi, mass
            )
    #calculate quasi-RRHO chemical potential at standard conditions
    #saver['chempot qRRHO'] = saver['chempot'] - calc_grimme(low_positive_freqs, temp) *temp
    saver['chempot qRRHO'] = saver['chempot'] - calc_grimme_short(low_positive_freqs, temp)

    #calculate RRHO chemical potential at low volume (only changes qtrans and chempot)
    (saver['qtrans V=1L'], _, _, _, saver['chempot V=1L']) = calc_partition_c(
            freqs, momi, mass, v=1e-3
            )
    #calculate quasi-RRHO chemical potential from chemical potential at low volume
    #saver['chempot V=1L qRRHO'] = saver['chempot V=1L'] - calc_grimme(low_positive_freqs, temp) *temp
    saver['chempot V=1L qRRHO'] = saver['chempot V=1L'] - calc_grimme_short(low_positive_freqs, temp)
    return saver

def calc_partition_c (allfreqs, mom_inert, mass, 
        sigma=SIGMA, temp=TEMPERATURE, n_part=MOLES, v=MOLES * R * TEMPERATURE / PRESSURE):
    """Formulas can be obtained from Mortimer Physical Chemistry chapter 21.

    However there is a mistake in TM7.3 (they do it correct but state it wrong)
    freqs is a numpy array, 
    zero point energy, 
    use v = n_part * R * temp / p  #m^3 for results at gaseous concentrations
    default for v is ideal gaeous volume. Use 1e-3 for concentration correction for fluids (1mol/L)
    """
    freqs = allfreqs[np.where(allfreqs > 1e-9)]
    freqs *= 100 *c*h#J
    mass = mass/N_A/1000#kg
    # now it is devided by N_A, N_A has to enter at some point and 
    #usually translational partition_c function is chosen.
    qtrans = (2*pi*mass*k*temp/h/h)**1.5 * v /n_part/N_A 
    qvib = np.prod(1/(1-np.exp(-freqs/k/temp)))
    qrot = pi**0.5 * ((8*pi*pi*k*temp/h/h)**3 
            *(mom_inert[0]*mom_inert[1]*mom_inert[2]*amu**3*a0**6))**0.5 /  sigma
    calczpe = 0.5 *  np.sum(freqs)*N_A/1000
    chempot = calczpe - R*temp*np.log(qtrans*qvib*qrot)/1000 
    return qtrans, qvib, qrot, calczpe, chempot

def calc_grimme_short (freq_cm, temp=TEMPERATURE):
    """Return value is added to the Gibbs free enthalpy 
    to obtain a qRRHO corrected Gibbs enthalpy.
    freq_cm : np array with vibrational frequencies in wavenumbers 
    """
    Bav = 1e-44#kg*m^2
    freq_s = freq_cm*100.0*c#1/s
    xx = freq_s*h/k/temp#no unit
    Sv = xx * (1.0 / (np.exp(xx)-1.0))  -  np.log(1.0 - np.exp(-xx))#no unit
    mue = h/(8.0 * pi**2.0 * freq_s)#J*s^2 = kgm^2
    Sr = (1 + np.log(8.0 *pi*pi*pi *mue*Bav / (mue + Bav) *k*temp /h/h) ) / 2#no unit
    w_damp = 1.0 / (1.0 + (1e2/freq_cm)**4)#m^4
    S_final = w_damp*R*Sv + ( (1.0-w_damp) *R*(1 + np.log(8.0*pi*pi*pi*mue*Bav /(mue + Bav) *k*temp/h/h) ) /2)#m^4*J/mol/K
    return np.sum((S_final - R*Sv )*milli)*temp#m^4*kJ/mol

def get_cosmors(ser, root, dat='out.tab'):
    with open(root+os.sep+dat) as file:
        for line in file:
            if 'out' in line:
                ser['CosmoRS'] = float(line[80:])

def get_eiger(ser, root, dat='eiger.out'):
    with open(root+os.sep+dat) as file:
        for line in file:
            if 'HOMO:' in line:
                ser['HOMO'] = float(line[28:39])
                ser['n_MO (HOMO)'] = float(line.split()[1])
            if 'LUMO:' in line:
                ser['LUMO'] = float(line[28:39])
                ser['n_MO (LUMO)'] = float(line.split()[1])

#parse energy file and get last single point, kinetic and potential energy
def get_energy(ser, root, dat='energy'):
    with open(root+os.sep+dat) as file:
        line = file.readlines()[-2]
        for i, cut in enumerate(['Single Point Energy', 'kin. E', 'pot. E'],1):
            ser[cut]=float(line.split()[i])
        ser['SPE kjmol'] = ser['Single Point Energy']*EH2KJMOL

#Regex searches for an integer and 3 floats
RE_ENERGY = re.compile("^[0-9 ]{6}\s+([-+]?\d*\.\d+)\s+([-+]?\d*\.\d+)\s+([-+]?\d*\.\d+)")#last one is element symbol
def get_energy2(root, dat='energy'):
    """returns vector with element[0]: total energy [1]:kinetic energy, [2]:potential energy"""
    with open(root+os.sep+dat) as file:
        print(file.readlines()[-2])
    with open(root+os.sep+dat) as file:
        return np.array(re.findall(RE_ENERGY, file.readlines()[-2])[0]).astype(float) #one D too many...

#Regex searches for 3 floats and one element symbol
RE_COORD = re.compile("([-+]?\d*\.\d+)[ ]+([-+]?\d*\.\d+)[ ]+([-+]?\d*\.\d+)[ ]+([a-z]{1,2})")
def get_coord3(root, dat='coord'):
    """Reads coord file and returns xyz coordinates in bohr"""
    with open(root+os.sep+dat) as file:
        #xyzelem = np.asarray(re.findall(RE_COORD, file.read().split('$')[1])) #we can also just read $coord
        xyzelem = np.asarray(re.findall(RE_COORD, file.read()))
        return xyzelem[:,:3].astype(float), xyzelem[:,3] #atomic units
        #return xyzelem[:,:3].astype(float)*BOHR2ANGSTROM, xyzelem[:,3]

def mass_of_elements(elems):
    """Takes list of element strings and converts the most frequently abundant isotope to the corresponding mass
    Probably it would be faster to write a dictionary but this is more convenient for now
    """
    return [Formula(elem.capitalize()).isotope.mass for elem in elems]

def center_of_mass(coords, mass):
    """takes np arrays of coordinates and masses and calculates center of mass from that"""
    return np.average(coords, axis=0, weights=mass)

def moment_of_inertia(coords,mass,i,j):
    """Calculates Moment of inertia for x(i=1,j=2), y(i=0,j=2) or z(i=0,j=1) direction
    coords : np.array with dimension (N,3) contains xyz coordinates of each atom.
    mass : np.array with dimension (N) containing molar mass of each atom.
    """
    return np.sum(mass * (coords[:,i]*coords[:,i]+coords[:,j]*coords[:,j]))

if __name__ == '__main__':
    main()
