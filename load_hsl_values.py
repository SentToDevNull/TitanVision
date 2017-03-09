default = [40, 130, 200, 255, 18, 255]


def get_bounds():
  try:
    with open("hslauto_values") as f:
      return map(int, f.read().split())
  except FileNotFoundError as e:
    print("Warning, file hslauto_values not found! Using default values")
    return default
