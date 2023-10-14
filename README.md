# AI Agent Bean
Agent Bean is AI agent that is designed to interact with users and perform various tasks. The initial focus is on coding but there are no limitations to other activities. 
It has been designed to be able to run local llm models available on the huggingface portal as well as interfacing with the openAI API so you can run the model fully localy if you need and have the available compute or use OpenAI API you can even mix booths if it make sense for you. As you can associate different models to different tasks.

It has a memory management system that can instantiate / dinstantiate models dependings on the needs of the task (it is still a bit rough )

Some of the code has been developped with the help of aider: https://github.com/paul-gauthier/aider (at the beginning while the code was less than 8k tokens)

## Curent capabilities:
The agent Bean is currently capable of the following:
- **Manage models**: manage the models and ability to instantiate / deinstantiate models, ability to use any transformers models 
- **Action Execution**: Agent Bean can perform various actions. The actions are defined in the setings file and can be easily extended. curently 

implemented actions:
  -  **summarize**: generate a summary of the provided text
  -  **search**: perform a search on the net
  -  **free**: freetext query
  -  **split**: split a task executable actions 
  -  **code**: generate code 
  -  **code_quality**: analyse the quality of the code (not yet working well)
  -  **requirements**: generate requirements
  -  **team_manager**: experimental agent to bheave as a team manager, to see how a llm could bheave as a manager 

The agent is continuously evolving, with new capabilities being added regularly.

## Current limitations:
- when modifying the settings fileit needs to be re uploaded for the changes to take effects
- It is not yet able to interact with files
- Load on 4 or 8 bit loading works except for GPTQ or GGML quantized models!? (they use a different proces for loading that needs to be implemented)
- Imprecise memory estimation for models
- display of system status ram / vram not working

Using local generation with transformers models:
- you need at least 16GB of video RAM to run 15B models in 4bits to be able to have correct coding and splitting result
- With 8GB V RAM you can run the 7B models in 4Bits however up to now their perfo is limited to perform proper codding and the model might not be able to generate theJSON for the splitting
- You may use a computer with less V RAM for testing purpose with 3B or 1.5B models but do not expect usefull results.


## WIP: Work in Progress:
- **Improve Model managment** Model memory estimation depending on model quantisation
- **Ability to perform action on files** to have an actual effect on code
- **improve transformers loading**: for 8 and 4 bits quantisation with GPTQ and GGML models
- **Actions backlog**: a backlog of actions to be executed
- **Ability to execute code in a sealed container**: to provide direct feedback to the agent
- **Context Management**: Agent Bean maintains a context of the conversation, which is used to generate relevant responses. It can add new elements to the context, clear the context, and manage the context length to ensure it stays within a specified token limit.
- **Document Loading**: Agent Bean can load a set of documents into a vectorstore for later use.
- **Model and Vectorstore Instantiation**: Agent Bean can instantiate different models and vectorstores based on the provided setup.

## Recent improvments:
- **Added settings file selection and loading**: to be able to easyly change the settings file
- **added a team_manager agent**: not totaly related to the rest but it is an experiment 
- **added requirements**: generate requirements
- **Make actions more generic** to allow beter variations from congig
- **Improve Model managment** Removed memory leak and improved model managment

## Useage:

Clone this repository:

`git clone https://github.com/kolergy/agent_bean.git`

Create an environement:

`conda create -n AB311 python=3.11`

Activate the environement:

`conda activate AB311`

Install the requirements:

`pip install -U -r requirements.txt`

Run the agent bean interface:

`python agent_bean_interface.py`


If you intent to use the openAI models you have to rename the template.env file as follows:

`cp template.env .env`

Then edit this .env file to insert your openAI API key 

Once edited you need to set the environement with:

`sourrce .env`

To test the code you can run the interface:

`python agent_bean_interface.py`
