# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# Python path setup
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Prague GTFS'
copyright = '2025, Nils Wüstefeld, Adam Pasálek'
author = 'Nils Wüstefeld, Adam Pasálek'
version = '0.1'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
