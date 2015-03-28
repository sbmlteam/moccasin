Quick start guide
=======================
Before learning what MOCCASIN does, it is important to know what it is. MOCCASIN is a python module stands for "Model ODE Converter for Creating Awesome SBML INteroperability". It is a project to develop a user-assisted converter that can take MATLAB or Octave ODE-based models in biology and translate them into SBML format. It can be run as a console application or used as a python module. 

###How do I install MOCCASIN?
Before you can use MOCCASIN, the libSBML Python module must be installed on your computer. For instructions on  how to do this, visit the SBML website downloads' [page](http://sbml.org/Software/libSBML/5.11.0/docs/formatted/python-api/libsbml-downloading.html#dl-python).

Then, you can simply use the setup script in this distribution to build and install MOCCASIN. To do so, simply run the following command from a terminal:

```python setup.py install```

>Please note that MOCCASIN will require having internet connection during installation and file conversion.

###How do I use MOCCASIN?
MOCCASIN exposes a command-line interface that allows users to convert MATLAB files into L3V1 SBML. For more information on how to use this, please refer to this [documentation](../scripts/README.md). 