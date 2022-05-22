# Reproduction attempt from the SwissRN ReproHack (original description further below)

We attempted to reproduce the analyes of the paper at the [SwissRN
ReproHack](https://www.reprohack.org/event/16/), see our [review](https://www.reprohack.org/review/71/) for details.
We were able to reproduce most analyses, but to get the analysis running we had to install some older
versions of Python and PyStan, as it did not work with newer versions (for
example, Pystan >= 3.0 is now imported with `import stan` and not with `import pystan`, 
so all code using the old import statement does not run anymore). While the paper reports the exact Python and
PyStan versions used, it does not for the other dependencies. In particular, the code does not 100% work with the newest
version of Pandas, so we had to modify the code at 2 places to get it running.

Peter was able to reproduce ca. 95% of the analysis on his local environment in the time that we had,
some MCMC sampling did not finish but we suspect that we would hav been successful if we had more time.
I tried to create a Docker container which recreates the computational environment used in the original
analysis. Assuming that Docker (with root rights) is installed, the Docker can be run by cloning this repository
and running `make` from the root folder of the repository. Since we ran out of time, we were not able 
to test whether all analyses reproduce successfully withing the Docker, but the first few MCMC 
chunks did, and so did the tables (after the previously mentioned tweak of the Pandas code). A future step could
be to indicate exactly which Pandas version was used in the original analysis, so that perhaps the
original code reproduces the original results.

# Measuring the impact of COVID-19 vaccine misinformation on vaccination intent in the UK and USA
*Sahil Loomba, Alexandre de Figueiredo, Simon Piatek, Kristen de Graaf, Heidi Larson*

This repository contains code and data for our paper in [*Nature Human Behaviour*](https://www.nature.com/articles/s41562-021-01056-1) on measuring the impact of exposure to COVID-19 vaccine misinformation on the intent to vaccinate in the UK and USA.

## Jupyter Notebooks
These notebooks are intended to aid importing, transforming, and analysing the survey data in this study. You may use [Jupyter nbviewer](https://nbviewer.jupyter.org/) to view these notebooks, or view their static (.html) versions in `.doc/`, or view them on OSF (note: OSF link currently hosts a preprint version of the manuscript).

1. `tables_figures.ipynb`: generates all figures and tables of the paper
2. `import_data.ipynb`: demo of reading and transforming survey data for use in any downstream statistical modeling; [~~view on OSF~~](https://osf.io/ej4c6/)
3. `statistical_analyses.ipynb`: demo statistical modeling and generation of figures and tables in the paper; [~~view on OSF~~](https://osf.io/b3qkc/)

## Directory Structure
1. `.dat/`: contains processed survey data; sufficient to run all statistical analyses in the paper
2. `.doc/`: contains full survey questionnaire and static (.html) versions of the Jupyter Notebooks
3. `.src/paper.py`: contains helper functions to generate all figures and tables of the paper
4. `.src/models.py`: contains functions to define and fit all Bayesian models described in the paper
5. `.src/utils.py`: contains helper functions to import and transform survey data, compute and plot posterior statistics
6. `.src/bayesoc.py`: defines python classes `Dim()`, `Outcome()`, `Society()` and `Model()` to implement general Bayesian socio-demographic models using [pystan](https://pystan.readthedocs.io/en/latest/)

## Links
1. View paper in [Nature Human Behaviour](https://www.nature.com/articles/s41562-021-01056-1)
2. View project on [GitHub](https://github.com/sloomba/covid19-misinfo/)
3. ~~View paper preprint on [medRxiv](https://www.medrxiv.org/content/10.1101/2020.10.22.20217513v1)~~
4. ~~View project on [OSF](https://osf.io/cxwvp/)~~

## Citation
Loomba, S., de Figueiredo, A., Piatek, S.J. et al. Measuring the impact of COVID-19 vaccine misinformation on vaccination intent in the UK and USA. *Nat Hum Behav* (2021). https://doi.org/10.1038/s41562-021-01056-1

