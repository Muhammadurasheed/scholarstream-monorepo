import os

def env_to_yaml(env_path, yaml_path):
    print(f"Reading {env_path}...")
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {env_path} not found!")
        return

    env_vars = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Handle simple KEY=VALUE
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Skip reserved Cloud Run variables
            if key == "PORT":
                continue
            
            # Remove quotes if present
            if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
                value = value[1:-1]
                
            env_vars[key] = value

    print(f"Writing {len(env_vars)} variables to {yaml_path}...")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        for key, value in env_vars.items():
            f.write(f'{key}: "{value}"\n')

def extract_frontend_vars(env_path):
    print(f"Reading frontend vars from {env_path}...")
    vars_list = []
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return ""

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Skip VITE_API_BASE_URL as we pass it explicitly from gcloud output
            if key == "VITE_API_BASE_URL":
                continue
                
            if key.startswith('VITE_'):
                 # Remove quotes if present
                if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
                    value = value[1:-1]
                vars_list.append(f"{key}={value}")
    
    return vars_list

def create_cloudbuild_yaml(project_id, service_name, backend_url, env_path='backend/.env'):
    # Base configuration
    steps = [
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": [
                "build",
                "-t", f"gcr.io/{project_id}/{service_name}",
                "-f", "Dockerfile.frontend",
                "--build-arg", f"VITE_API_BASE_URL={backend_url}"
            ]
        }
    ]
    
    # Add frontend env vars as build args
    if os.path.exists('.env'):
        vars_list = extract_frontend_vars('.env')
        for var in vars_list:
            steps[0]["args"].extend(["--build-arg", var])
            
    steps[0]["args"].append(".")
    
    cloudbuild = {
        "steps": steps,
        "images": [f"gcr.io/{project_id}/{service_name}"]
    }
    
    # Write to yaml file
    import json
    # We use JSON format which is valid YAML (mostly) but easier to write correctly from python
    # actually let's write simple psuedo-yaml to avoid pyyaml dependency
    
    with open('cloudbuild.yaml', 'w') as f:
        f.write("steps:\n")
        f.write(f"  - name: '{steps[0]['name']}'\n")
        f.write("    args:\n")
        for arg in steps[0]['args']:
            # escape single quotes if needed
            safe_arg = arg.replace("'", "''")
            f.write(f"      - '{safe_arg}'\n")
            
        f.write("images:\n")
        f.write(f"  - '{cloudbuild['images'][0]}'\n")

if __name__ == "__main__":
    import sys
    
    # Mode 1: Backend Env (default)
    if len(sys.argv) == 1:
        # Path to backend .env
        env_path = 'backend/.env'
        if not os.path.exists(env_path) and os.path.exists('.env'):
            env_path = '.env'
        env_to_yaml(env_path, 'env.yaml')
        
    # Mode 2: Generate CloudBuild (called with args)
    elif len(sys.argv) == 4:
        project_id = sys.argv[1]
        service_name = sys.argv[2]
        backend_url = sys.argv[3]
        create_cloudbuild_yaml(project_id, service_name, backend_url)


