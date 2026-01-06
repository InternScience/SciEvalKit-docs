# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

source_encoding = 'utf-8-sig'
project = 'SciEvalKit'
copyright = '2025, SciEvalKit'
author = 'SciEvalKit'
release = '0.1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['recommonmark',"myst_parser",]
source_suffix = {'.rst': 'restructuredtext',
                 '.md':  'markdown'}

templates_path = ['_templates']
exclude_patterns = []

language = 'zh_CN'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

import sphinx_rtd_theme
html_theme = "sphinx_rtd_theme"

# The master toctree document.
master_doc = 'index'