import os
os.system('python setup.py sdist bdist_wheel')
os.system('twine upload --username __token__ --password pypi-AgEIcHlwaS5vcmcCJGI0ZDRkMzA1LTNhMjUtNDQxNC1iYTQ3LTNlMTdiYmNiNTgwZAACKlszLCIxOWUxYTc5Ny01OTU0LTQ5YzktYTk2Ni05YmFmYTU2ZjVlNjQiXQAABiCl39B04xKCIgxE4VVDpu-rmA0d2HRCrpCLj31uztrdYA dist/*')