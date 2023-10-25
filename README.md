# CATMA: Conformance Analysis Tool for Microserivce Applications 
[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## About
This is a tool for performing automated conformance analysis between the implementation and deployment of microservice applications. The tool takes as input a model derived by performing static analysis on the microservice application and models derived by performing dynamic analysis on the log traces collected from the microservice application. Currently, the tool accepts Dataflow Diagrams (DFD) as the input static model and State Machines as the input dynamic models. The tool performs conformance analysis by means of computing differences between the DFD and the State Machine models. We define the differences as non-conformances between the implementation and deployment of the microservice application. The tool generates outputs that would provide the following insights on the detected non-conformances:
- A high-level visualization showing how many, which type, and where non-conformances are detected in the microservice application.
- Potential interpretations, presented in a human-readable format, aiding the user with the understanding what are the potential underlying causes of the detected non-conformances. 

### Workflow Architecture 
CATMA consists of 5 components: the ***Model-processor*** (1) parses the input models (static and dynamic) to extract architectural components. The obtained data is passed on to the
***Non-conformance Detector*** (2), which checks whether there are any discrepancies between the two input models. If a non-conformance is detected, it is forwarded to both the ***Interpretation Generator*** (3) and the ***Non-conformance Visualizer*** (4). The latter (3) collects all detected non-conformances and generates a model-based visualization, showing the non-conformances in the system’s architecture. The former (3) generates a set of possible interpretations for each detected non-conformance, which describe potential causes. These interpretations are forwarded to the ***Interpretation Visualizer*** (5), which generates HTML pages that visualize the interpretations. CATMA is designed to be modular, meaning that each component presented in the workflow can be replaced or expanded to fit its user’s needs.

## Requirements and Installation
The tool is completely written in Python and thus a Python installation is required to run the tool. Though the tool is tested with Python 3.9, it should work with any version of Python 3. Besides Python, the tool requires the following Python packages to be installed:
- pandas (version 1.3.5 or higher)
- numpy (version 1.20.0 or higher)
- tqdm (version 4.62.3 or higher)
- jsonschema (version 3.2.0 or higher)
- graphviz (version 0.16 or higher)
- dominate (version 2.7.0 or higher)
- pydot (version 1.4.2 or higher)
- plantuml (version 0.3.0 or higher)

All above Python packages can be easily installed using the `requirements.txt` file provided in this repository. To install the required packages, run the following command from the root directory of this repository:
```
pip install -r requirements.txt
```

After installing the required packages, one should already be able to run the tool. 

Besides the above Python packages, the tool requires an internet browser to be installed on the system. The browser is handy for viewing the interpretations generated for the detected non-conformances. The tool was tested with the Google Chrome browser but should work with any other browser as well.


## Example Usage
The tool can be run via the command line. The main Python script that should be run is `CATMA.py`. This script takes only three arguments, namely:
- `static_model_path`: used for providing the path to the DFD model extracted from performing static analysis on the microservice application.
- `dynamic_models_path`: used for providing the path to the State Machine models extracted from performing dynamic analysis on the microservice application.
- `output_path`: used for providing the path to the directory where the outputs of the tool should be stored.


**Before running the tool**, make sure that you have specified the names of the services and the name of the general dynamic model for the target microservice application in the `config.json` file (located in the `config` folder). The general dynamic model is the model that was inferred from all network communication log data collected for the microservice application. The name of the services and the general dynamic model should be specified using the `services` and `general_dynamic_model` fields respectively in the JSON file. As an example, the `config.json` file for `ewolff/microservice` is shown below:

```
{
    "services" : ["catalog", "order", "customer", "turbine", "zuul", "eureka", "user"],
    "general_dynamic_model" : "ms_http_data"
}
```

Once configuration is set for the MSA, one can run the tool by executing the following command from the root directory of this repository:
```
python CATMA.py --static_model_path <PATH_TO_STATIC_MODEL> --dynamic_models_path <PATH_TO_DYNAMIC_MODELS> --output_path <PATH_TO_OUTPUT_DIRECTORY>
```

Using `ewolff/microservice` as an example, you can run the tool with the following command:
```
python CATMA.py --static_model_path ./data/ewolff_microservice/ewolff_microservice_static_model.json --dynamic_models_path ./data/ewolff_microservice/dynamic_models/ --output_path ./output/
```

Once the command has been run, you should see terminal output similar to what is shown below:
![](https://github.com/tudelft-cda-lab/CATMA/blob/main/example_terminal_output.gif)

## Example use-case of CATMA
In the evaluation of CATMA, the tool identified the (dynamic) non-conformance that was mentioned on the README of [`ewolff/microservice`](https://github.com/ewolff/microservice/blob/master/README.md). The author has reported the missing communication behavior between `order` and `turbine`. After running a conformance analysis on the application and inspecting the generated interpretations, we managed to identify the cause for the missing behavior between the two services; a misconfiguration in the [Hystrix](https://github.com/Netflix/Hystrix) monitoring dashboard prevented stream data from being visualized as it was intended in the implementation. We notified the developer and our [fix](https://github.com/ewolff/microservice/pull/30) was accepted.

### Test out the fix for `ewolff/microservice`
To validate that the dynamic non-conformance has been fixed in `ewolff/microservice`, you can run a conformance analysis on the application after the fix using the following command:

```
python CATMA.py --static_model_path ./data/ewolff_microservice/ewolff_microservice_static_model.json --dynamic_models_path ./data/ewolff_microservice/dynamic_models_after_fix/ --output_path ./output/
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
