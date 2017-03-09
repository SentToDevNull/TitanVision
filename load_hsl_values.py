default = [40, 130, 200, 255, 18, 255]


def get_bounds():
  try:
    result = {}
    with open("hslauto_values") as f:
      for line in f:
        params = list(map(int, line.split()))
        result[params[0]] = params[1:]
      return result
  except FileNotFoundError as e:
    print("Warning, file hslauto_values not found! Using default values")
    return default
