from typing import List, Dict, Any, Union
import logging
import acai.cache_query.helper as helper

class ValidateQuery:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    # ¦ validate_patterns
    def validate_patterns(self, pattern: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        validation_results: List[Dict[str, Any]] = []

        patterns = pattern if isinstance(pattern, list) else [pattern]

        for item in patterns:
            validation_result = self._validate_pattern(item)
            if validation_result:
                validation_results.append({
                    "pattern": item,
                    "validation_errors": validation_result
                })

        return validation_results

    # ¦ _validate_pattern
    def _validate_pattern(self, pattern: Dict[str, Any]) -> List[str]:
        def evaluate_pattern(validation_results: List[str], prefix: str, pattern: Dict[str, Any]) -> None:
            valid_keys = ['accountId', 'accountName', 'accountTags', 'ouId', 'ouIdWithPath', 'ouName', 'ouNameWithPath', 'ouTags']
            if not helper.is_valid_json_key_only(pattern, valid_keys):
                validation_results.append(
                    f'Section "{prefix}": An account-context may only contain the keys "accountId", "accountName", "accountTags", "ouId", '
                    '"ouIdWithPath", "ouName", "ouNameWithPath", "ouTags". Please be aware, that the elements are treated with a logical AND.'
                )

        def evaluate_exclude(validation_results: List[str], exclude_json: Any) -> None:
            if exclude_json == ['*']:
                self.response_hints.append(
                    'In a "policyScope"-section {"exclude": ["*"]} can be written as {"exclude": "*"}.'
                )
            elif isinstance(exclude_json, list):
                for account_scope_element in exclude_json:
                    if isinstance(account_scope_element, dict):
                        evaluate_pattern(validation_results, "exclude", account_scope_element)
            elif isinstance(exclude_json, dict):
                evaluate_pattern(validation_results, "exclude", exclude_json)
            elif exclude_json != '*':
                validation_results.append(
                    'A "accountScope.exclude" section may only be "*" for excluding all accounts, a single account-context '
                    'or a list of account-contexts that will be evaluated with a logical OR.'
                )

        def evaluate_force_include(validation_results: List[str], force_include_json: Any) -> None:
            if isinstance(force_include_json, list):
                for account_scope_element in force_include_json:
                    if isinstance(account_scope_element, dict):
                        evaluate_pattern(validation_results, "forceInclude", account_scope_element)
            elif isinstance(force_include_json, dict):
                evaluate_pattern(validation_results, "forceInclude", force_include_json)
            else:
                validation_results.append(
                    'A "accountScope.forceInclude" may only be a single account-context or a list of account-context that will be evaluated with a logical OR.'
                )

        validation_results: List[str] = []
        if 'exclude' not in pattern:
            validation_results.append(
                'A "policyScope.accountScope" section must contain an exclude-section.'
            )

        if helper.get_value(pattern, 'forceInclude') in ['*', ['*']]:
            self.response_hints.append(
                'In a "policyScope"-section "forceInclude": "*" or "forceInclude": ["*"] is not required, as by default all entities are in scope.'
            )

        if helper.contains_key(pattern, 'forceInclude') and not helper.contains_key(pattern, 'exclude'):
            validation_results.append(
                'By default all AWS accounts are in scope. A "policyScope"-section that wants to forceInclude AWS accounts first must exclude AWS accounts.'
            )

        if helper.contains_key(pattern, 'exclude'):
            evaluate_exclude(validation_results, helper.get_value(pattern, 'exclude'))

        if helper.contains_key(pattern, 'forceInclude'):
            evaluate_force_include(validation_results, helper.get_value(pattern, 'forceInclude'))

        return validation_results


def is_valid_json_key_any(json_object: Dict[str, Any], allowed_keys: List[str]) -> bool:
    """
    Check if the JSON object contains only allowed_keys as keys (case insensitive).
    
    :param json_object: The JSON object to validate.
    :param allowed_keys: The list of allowed keys.
    :return: True if all keys in the JSON object are allowed, False otherwise.
    """
    json_keys_lower = {key.lower() for key in json_object.keys()}
    allowed_keys_lower = {key.lower() for key in allowed_keys}
    return json_keys_lower.issubset(allowed_keys_lower)

def is_valid_json_key_only(json_object: Dict[str, Any], allowed_keys: List[str]) -> bool:
    """
    Check if the JSON object contains any of the allowed_keys and nothing else (case insensitive).
    
    :param json_object: The JSON object to validate.
    :param allowed_keys: The list of allowed keys.
    :return: True if the JSON object contains only allowed keys and nothing else, False otherwise.
    """
    json_keys_lower = {key.lower() for key in json_object.keys()}
    allowed_keys_lower = {key.lower() for key in allowed_keys}
    return json_keys_lower.issubset(allowed_keys_lower) and bool(json_keys_lower)

def str_to_bool(s: str) -> bool:
    """
    Convert a string representation of truth to boolean.
    
    :param s: The string to convert.
    :return: True if the string represents a truth value, False otherwise.
    """
    return s.lower() in ['true', '1', 't', 'y', 'yes']

def contains_key(json_object: Dict[str, Any], key: str) -> bool:
    """
    Check if a key exists in the JSON object (case insensitive).
    
    :param json_object: The JSON object to check.
    :param key: The key to search for.
    :return: True if the key exists in the JSON object, False otherwise.
    """
    return key.lower() in {k.lower() for k in json_object.keys()}

def get_value(json_object: Dict[str, Any], key: str) -> Any:
    """
    Get the value associated with a key in the JSON object (case insensitive).
    
    :param json_object: The JSON object to search.
    :param key: The key whose value is to be retrieved.
    :return: The value associated with the key if it exists, an empty dictionary otherwise.
    """
    for k, v in json_object.items():
        if k.lower() == key.lower():
            return v
    return {}
