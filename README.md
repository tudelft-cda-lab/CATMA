# CATMA: Conformance Analysis Tool for Microserivce Applications 
[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## About
This is a tool for performing automated conformance analysis between implementation and deployement of microservice applications. The tool takes as input a model derived by performing static analysis on the microservice application and models derived by performing dynamic analysis on the log traces collected from the microservice application. Currently, the tool accepts Dataflow Diagrams (DFD) as the input static model and State Machines as the input dynamic models. The tool performs conformance analysis by means of computing differences between the DFD and the State Machine models. We define the differeces as non-conformances between implementation and deploymenent of the microservice application. The tool generates outputs that would provide the following insights on the deteted non-conformances:
- A high-level visualization showing how many, which type, and where non-conformances are detected in the microservice application.
- Potential interpretations, presented in a human-readable format, aiding the user with the understanding what are the potential underlying causes of the detected non-conformances. 

## Requirements and Installation
The tool is completely written in Python and thus a Python installation is required to run the tool. Though the tool is tested with Python 3.9, it should work with any version of Python 3. Besides Python, the tool requires the following Python packages to be installed:
- pandas (version 1.3.5 or higher)
- numpy (version 1.20.0 or higher)
- tqdm (version 4.62.3 or higher)
- jsonschema (version 3.2.0 or higher)
- graphviz (version 0.16 or higher)
- dominate (version 2.7.0 or higher)
- pydot (version 1.4.2 or higher)

All above Python packages can be easily installed using the `requirements.txt` file provided in this repository. To install the required packages, run the following command from the root directory of this repository:
```
pip install -r requirements.txt
```

After installing the required packages, one should already be able to run the tool. 

Besides the above Python packages, the tool requires an internet browser to be installed on the system. The browser is handy for viewing the interpretations generated for the detected non-conformanes. The tool was tested with Google Chrome browser, but should work with any other browser as well.

## Example Usage
The tool can be run via the command line. The main Python script that should be run is `conformance_analysis.py`. This script takes only three arguments, namely:
- `static_model_path`: used for providing the path to the DFD model extracted from performing static analysis on the microservice application.
- `dynamic_models_path`: used for providing the path to the State Machine models extracted from performing dynamic analysis on the microservice application.
- `output_path`: used for providing the path to the directory where the outputs of the tool should be stored.

One can run the tool by executing the following command from the root directory of this repository:
```
python conformance_analysis.py --static_model_path <PATH_TO_STATIC_MODEL> --dynamic_models_path <PATH_TO_DYNAMIC_MODELS> --output_path <PATH_TO_OUTPUT_DIRECTORY>
```

For example, you can run the tool on the application ewolff/microservice with the following command:
```
python conformance_analysis.py --static_model_path ./data/ewolff_microservice/ewolff_microservice_static_model.json --dynamic_models_path ./data/ewolff_microservice/dynamic_models/ --output_path ./output/
```

## Citing this work
If you use this tool in your research, please cite the following paper:
```
@inproceedings{cao2023catma,
  title={CATMA: Conformance Analysis Tool for Microservice Applications},
  author={Cao, Clinton and Schneider, Simon, and Diaz Ferreyra, Nicolás, and Verwer, Panichella, Annibale and Verwer, Sicco and Scandariato, Riccardo},
  publisher={ACM},
  year={2023}
}
```

## Acknowledgements
This tool is developed within the context of the [AssureMOSS project](https://assuremoss.eu), which has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No. 952647.
