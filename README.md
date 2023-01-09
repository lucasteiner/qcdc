# qcdc 
this directory is for data collection of turbomole calculations,
a short discription of programs and how to use is given here.
pandas is used for everything, it will help you a lot.

freq.sh
The shell script will call the main programs until everything is collected or updated

folder_names.py
Here directory names are saved for later which can be used for accessing the directories,
directory names have to be changed in this file
the declared variables are then written to main.dat, which contains the names, so bash scripts can access them easily.
This directories are the main directories, 
the script freq.sh will then go into these directories and read all directories located there 
and write them to names_f, which are read by the mainprogram again.

init_var.py
declares the names of the columns of the dataframe,
names can be changed in the file.

freeh.err freeh_in
output and input file of calculations of thermodynamic properties,
in the directories a freeh.out file is generated, which is read by the program

collect_data.py
this is the main program for collection of data in different directories,
it will write everything to one big "data.csv" sheet, which then can be observed by the programs in the directories.
for observation it is most convinient to use pandas, and not excel.

example directories with programs called data.py,
a small .csv file for excel or .tex for LaTeX can be generated easily.
numforce
pbe0m06_struc789
time
damping
fermi

###
Verbesserungen:
main programme aus dem Modul entfernen
uebrig bleiben nur functions und evtl ein beispiel fuer main.py/sh


###
Neues Ziel ist:
1. Funktion
1x Bash Skript das alle directories mit tree in ein file schreibt und 
Turbomole Funktionen verwendet und die Dirs aktualisiert.
Terminal commands wie t2x -c > last-geo.xyz, freeh < """ """ sollten hier drin stehen,
und bestenfalls mit optionen mitaufgerufen werden.

2. Funktion
ist das collection.py skript. 
Es ist im besten Fall auch unabhaengig verwendbar, 
das sollte mit der Zeile [x[0] for x in os.walk(directory)]
oder next(os.walk('.'))[1] machbar sein.
Es parst alle files in den Directories des Directorylistings und schreibt die Daten in ein .csv-file.

#IDEAS
save coordinate-links in one column and coordinate files (t2energy) in one directory
OR
create one entry for each atom for
-x
-y
-z
-basis-set
-charge1
-charge2
...
