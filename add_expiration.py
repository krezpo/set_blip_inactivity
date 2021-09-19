import glob
import json
import sys
import yaml

ENCODING = "UTF-8"

def has_expiration_condition(condition_outputs):

    for condition in condition_outputs:

        conditions = condition['conditions'][0]

        if conditions['source'] == 'input' and conditions['comparison'] == 'notExists' and conditions['values'] == []:
           
           return True 

    return False

def format_inactivity_states(states, chatbot, context, destination):

    # Primeiro Bloco
    states["4ceeb9c3-a5e5-4b5a-9468-352fb3ddf525"]["$enteringCustomActions"][0]["settings"]["context"]["value"] = context
    states["4ceeb9c3-a5e5-4b5a-9468-352fb3ddf525"]["$enteringCustomActions"][0]["settings"]["address"] = destination

    # Segundo Bloco
    states["e3bfe3f0-2cfd-4076-a708-fc209bf297ff"]["$enteringCustomActions"][0]["settings"]["action"] = chatbot
    states["e3bfe3f0-2cfd-4076-a708-fc209bf297ff"]["$enteringCustomActions"][1]["settings"]["category"] = "Inatividade - {}".format(chatbot)
    
    return states

def get_expiration_state_id(states):

    expiration_state_id = list(states.keys())[-1]

    return expiration_state_id

def get_expiration_condition(expriration_state_id):

    expiration_condition = {"stateId": expiration_state_id,
			                "conditions": [{"source": "input",
				                            "comparison": "notExists",
				                            "values": []}],
			                "$invalid": False}

    return expiration_condition

if __name__ == "__main__":

    with open("config.yml") as yaml_file:
        config = yaml.load(yaml_file, Loader=yaml.SafeLoader)

    if config == None:
        sys.exit(-1)

    chatbots = glob.glob("{}/*.json".format(config["source_folder"]))

    for chatbot in chatbots:
        print(chatbot)

        with open(chatbot, 'r', encoding=ENCODING) as data:
            builder = json.load(data)

        with open(config["inactivity_states"], 'r', encoding=ENCODING) as data:
            chatbot_name = str(chatbot.split("/")[-1]).replace(".json", "")
            states = format_inactivity_states(states = json.load(data), chatbot = chatbot_name, context = config["context_message"], destination = config["destination_service"])
            expiration_state_id = get_expiration_state_id(states)
            expiration_condition = get_expiration_condition(expiration_state_id)

            for state in states:
                builder[state] = states[state]
        
        for state in builder:
            if state in ("onboarding", expiration_state_id):
                continue

            if "desk:" in state:
                continue

            for action in builder[state]["$contentActions"]:

                if 'input' in action:
                    if action['input']['bypass'] == False:
                        action['input']['expiration'] = config["expiration_interval"]

                        if not has_expiration_condition(builder[state]["$conditionOutputs"]):
                            builder[state]["$conditionOutputs"].append(expiration_condition)
                            print("Inseriu inatividade em {}".format(builder[state]["$title"]))
        
        with open("{}/{}.json".format(config["destination_folder"], chatbot_name), "w+", encoding=ENCODING) as output:
            json.dump(builder, output, indent=4, ensure_ascii=False)