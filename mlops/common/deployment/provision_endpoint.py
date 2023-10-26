
import json
import argparse
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint
)
from azure.identity import DefaultAzureCredential


parser = argparse.ArgumentParser("provision_endpoints")
parser.add_argument("--subscription_id", type=str, help="Azure subscription id", required=True)
parser.add_argument("--output_file", type=str, help="outfile file needed for endpoint principal", required=True)
parser.add_argument("--build_id", type=str, help="build id for deployment", required=True)
parser.add_argument("--environment_name",type=str,help="environment name (e.g. dev, test, prod)", required=True)
parser.add_argument("--model_type", type=str, help="name of the flow", required=True)
args = parser.parse_args()


build_id = args.build_id
output_file = args.output_file
stage = args.environment_name
model_type = args.model_type
main_config = open(f"{model_type}/config.json")
model_config = json.load(main_config)

for obj in model_config["envs"]:
    if obj.get("ENV_NAME") == stage:
        config = obj
        break

resource_group_name = config["RESOURCE_GROUP_NAME"]
workspace_name = config["WORKSPACE_NAME"]
real_config = f"{model_type}/configs/deployment_config.json"


ml_client = MLClient(
    DefaultAzureCredential(), args.subscription_id, resource_group_name, workspace_name
)


config_file = open(real_config)
endpoint_config = json.load(config_file)
for elem in endpoint_config['azure_managed_endpoint']:
    if 'ENDPOINT_NAME' in elem and 'ENV_NAME' in elem:
        if stage == elem['ENV_NAME']:
            endpoint_name = elem["ENDPOINT_NAME"]
            endpoint_desc = elem["ENDPOINT_DESC"]
            endpoint = ManagedOnlineEndpoint(
                name=endpoint_name,
                description=endpoint_desc,
                auth_mode="key",
                tags={"build_id": build_id},
            )

            ml_client.online_endpoints.begin_create_or_update(endpoint=endpoint).result()

            principal_id = ml_client.online_endpoints.get(endpoint_name).identity.principal_id
            if output_file is not None:
                with open(output_file, "w") as out_file:
                    out_file.write(str(principal_id))
