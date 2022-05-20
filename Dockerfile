FROM python:3.7.3

# upgrade pip
RUN python3 -m pip install --upgrade pip

# install python dependencies
RUN python3 -m pip install numpy pandas matplotlib cython

# install pystan
RUN python3 -m pip install pystan==2.17.1.0

# install jupyter notebook
RUN python3 -m pip install jupyter

# copy files
RUN mkdir analysis
COPY ./ analysis
WORKDIR analysis

# run jupyter notebook
CMD jupyter notebook --port=8889 --ip 0.0.0.0 --allow-root --no-browser
