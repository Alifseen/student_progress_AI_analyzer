import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import json

def flatten_data(data: dict) -> dict:
    flat_dict = {}

    for k,v in data.items():
        if k != "Full Length Exams - Section Wise":
            for k1, v1 in v.items():
                for k2, v2 in v1.items():
                    if k2 == 'summary':
                        for k3, v3 in v2.items():
                            if k1 in flat_dict.keys():
                                flat_dict[k1].update(
                                    {k3: v3['Avg Score for Attempted Tests'] * (v3['Completion'] / 100)})
                            else:
                                flat_dict[k1] = {
                                    k3: v3['Avg Score for Attempted Tests'] * (v3['Completion'] / 100)}
    return flat_dict


def generate_df(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    flat_dict = flatten_data(data)

    df = pd.DataFrame.from_dict(flat_dict, orient='index')

    return df


def generate_heatmap(file_path, output_path, title: str, size):
    colors = ['#0C203B', '#2D72D2', '#EAF1FB']

    custom_cmap = LinearSegmentedColormap.from_list(
        'Blue Shades',
        colors,
        N=256
    )

    plt.figure(figsize=size)
    plt.title(title,
              fontsize=20,
              pad=23,
              )

    ax = sns.heatmap(generate_df(file_path),
                     vmin=0.0,
                     vmax=100.0,
                     cmap=custom_cmap,
                     annot=True,
                     fmt='.1f',
                     cbar_kws={'label': 'Progress (%)'})

    ax.set(xlabel="Difficulty Level", ylabel="Topics")

    ax.xaxis.tick_top()
    ax.tick_params(axis='x', labelsize=12)

    ax.tick_params(axis='y', labelsize=10)

    ax.xaxis.set_label_position('top')
    ax.xaxis.label.set_size(16)
    ax.xaxis.labelpad = 15

    ax.yaxis.label.set_size(16)
    ax.yaxis.labelpad = 10

    plt.savefig(output_path,
                bbox_inches='tight')

    plt.close()

    return "Heatmap Saved"