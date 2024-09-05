from typing import Tuple, Sequence, Callable

from krules_core.subject.storaged_subject import Subject

#from strategies.strategy import get_subject


def set_verb(verb: str | None, subject: Subject = None) -> str | None:
    #if subject is None:
    #    subject = get_subject()
    assert (verb in ["Buy", "Sell", None])
    _, old_verb = subject.verb = verb
    return old_verb


def get_verb_from(
        strategies: Sequence[Callable[[float, Subject | None], Tuple[str, str | None]] | Tuple[str, str | None]],
        _for: float = None, subject: Subject = None) -> Tuple[str | None, dict]:
    """
  This function takes a list of callables representing trading strategies
  and returns a single verb ("Buy" or "Sell") if all strategies agree on
  the same suggestion, excluding those returning None. Otherwise, it returns None.

  Args:
      strategies: A list of callables representing trading strategies.
      _for: The price for which the verb should be returned
      subject: The strategy subject

  Returns:
      A string representing the agreed-upon verb ("Buy" or "Sell") or None if there's no consensus, plus all results.
  """

    strategy_results = {}
    for strat in strategies:
        name, result = callable(strat) and strat(price=_for, subject=subject) or strat
        strategy_results[name] = result

    # Filter out strategies that don't suggest anything ("*") based on the dictionary
    filtered_strategies = [strat for strat in strategy_results if strategy_results[strat] is not None]

    # Check if there are any remaining strategies after filtering
    if not filtered_strategies:
        return None, strategy_results

    # Get the first strategy's suggestion from the dictionary
    reference_verb = strategy_results[filtered_strategies[0]]

    # Check if all remaining strategies agree with the reference verb (using dictionary values)
    for strat in filtered_strategies[1:]:
        if strategy_results[strat] != reference_verb:
            return None, strategy_results

    # If all strategies agree, return the agreed verb
    return reference_verb, strategy_results


def is_opposite(verb1, verb2) -> bool:
    return verb1 == "Buy" and verb2 == "Sell" or verb1 == "Sell" and verb2 == "Buy"
