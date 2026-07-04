import traceback

try:
    import main
    print("Main loaded successfully")
except Exception as e:
    print("ERROR LOADING MAIN:")
    traceback.print_exc()
