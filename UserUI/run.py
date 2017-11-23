###########################################################
# File:		run.py
# Authors:	Irfan Khan				 999207665
#		   	Larissa Ribeiro Madeira 1003209173
# Date:		October 2017
# Purpose: 	Website Entrypoint
###########################################################
#!venv/bin/python
from app import webapp
webapp.run('0.0.0.0',5000, debug=True)