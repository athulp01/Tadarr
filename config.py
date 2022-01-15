import yaml
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.yaml")

config = yaml.safe_load(open(CONFIG_PATH, encoding="utf8"))

def flatten_dict(dd, separator ='/', prefix =''):
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }

def checkConfig():
    missingConfig=[]
    for key_ex, value_ex in flatten_dict(config_example).items():
        if key_ex not in flatten_dict(config):
            missingConfig.append(key_ex)
    return missingConfig
