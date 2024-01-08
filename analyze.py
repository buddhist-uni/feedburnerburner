#!/bin/python3

import yaml
from utils import (
   prompt,
   checklist_prompt,
   radio_dial,
)
from main import (
    SETTINGS_FILE,
    yaspin,
    db_dir,
    settings,
)
from models import (
   ALL_MODELS,
)
from models.base import (
   Corpus,
   ModelStatus,
)
from models.feed import (
   FeedEntry,
)

HELP_STRING = """
INSTRUCTIONS:
1. Select a model to initialize it.

2. Once initialized, the model will summarize its accuracy with a string like:
   (P=20% R=100% => 45%)
This means that the model estimates its Precision (True Positive Rate) at 20%
and its Recall (1 - False Negative Rate) at 100% for a total "accuracy" of
sqrt(P*R) => 45%

3. Once initialized, select a model a second time to choose it as your feed filter

MODELS:
""" + '\n'.join([f"- {model.NAME} Model\n  {model.DESCRIPTION}" for model in ALL_MODELS]) + "\n"

if __name__ == '__main__':
   corpus = Corpus()
   with yaspin(text='Loading...'):
      for fd in db_dir.iterdir():
         if fd.name.endswith('.json'):
            corpus.add_entry(FeedEntry(json_file=fd))
   models = [MC(corpus) for MC in ALL_MODELS]
   while True:
      print("Choose a model:")
      options = [f"{model.NAME} ({model.get_status_summary()})" for model in models]
      options.extend(["Help", "Exit (No change)"])
      selection = radio_dial(options)
      if selection < len(models):
         selected_model = models[selection]
         if selected_model.status == ModelStatus.Invalid:
            print(f"This model requires at least {selected_model.MIN_DATA} to use.")
            continue
         if selected_model.status == ModelStatus.Unanalyzed:
            selected_model.analyze()
         if selected_model.status == ModelStatus.Analyzed:
            if selected_model.is_refinable() and prompt("Would you like to refine this model?"):
               selected_model.refine()
            if prompt("Use this model for your feed filter?"):
               settings['algo'] = selected_model.__class__.__name__
               settings['algo_params'] = selected_model.get_parameters()
               SETTINGS_FILE.write_text(yaml.dump(settings))
               print("Settings saved! Enjoy your feed :)")
               quit(0)
            continue
      selection -= len(models)
      match selection:
         case 0:
            print(HELP_STRING)
            continue
         case 1:
            quit(0)
