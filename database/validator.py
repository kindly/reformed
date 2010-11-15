import formencode
from validators import All

def validator(data, schema_dict, state = None):

    schema = formencode.Schema(allow_extra_fields = True,
                             ignore_key_missing = True,
                             **schema_dict)
    ##FIXME make form tokens better so we dont need this.
    data_to_validate = {}

    for key in schema_dict.iterkeys():
        ##FIXME do we get a value for all keys?
        value = data.get(key)
        data_to_validate[key] = value

    return schema.to_python(data_to_validate, state)

def validation_rules(schema_dict):

    schema = {}

    for key, value in schema_dict.iteritems():
        if key == "chained_validators":
            continue
        if not isinstance(value, All):
            continue
        all_info = []


        for validator in value.validators:
            validator_info = {}

            validator_info["type"] = validator.__class__.__name__

            for name, attrib in validator.__dict__.iteritems():
                if name in ('declarative_count', 'inputEncoding', 'outputEncoding'):
                    continue
                if name.startswith("_"):
                    continue
                validator_info[name] = attrib

            all_info.append(validator_info)

        schema[key] = all_info

    return schema

