import pandas as pd
import matplotlib.pyplot as plt

from soils_revealed.data_params import GEEData

dataset = GEEData('Global-Land-Cover')


def get_data(ds):
    df = ds.isel(time=0).to_dataframe().reset_index().drop(
        columns=['x', 'y', 'time']).rename(
        columns={'stocks': 'stocks_2000', 'land-cover': 'land-cover_2000'})

    df = pd.concat([df,
                    ds.isel(time=1).to_dataframe().reset_index().drop(
                        columns=['x', 'y', 'time']).rename(
                        columns={'stocks': 'stocks_2018', 'land-cover': 'land-cover_2018'})], axis=1)

    # Filter rows where columns A and B have equal values
    df = df[df['land-cover_2000'] != df['land-cover_2018']]
    df['stocks_change'] = df['stocks_2018'] - df['stocks_2000']
    df = df[df['stocks_change'] != 0.]
    df = df[['land-cover_2018', 'land-cover_2000', 'stocks_change']]
    df['land-cover_2000'] = df['land-cover_2000'].apply(
        lambda x: dataset.class_group_names()[str(x)])
    df['land-cover_2018'] = df['land-cover_2018'].apply(
        lambda x: dataset.class_group_names()[str(x)])

    # Grouping the DataFrame by 'land-cover_2000' and 'land-cover_2018' and summing 'stocks_change'
    grouped_df = df.groupby(['land-cover_2000', 'land-cover_2018'])['stocks_change'].sum().reset_index()
    grouped_2018_df = grouped_df.groupby(['land-cover_2018'])['stocks_change'].sum().reset_index()

    data = {}
    for category in grouped_2018_df.sort_values('stocks_change')['land-cover_2018']:
        records = grouped_df[grouped_df['land-cover_2018'] == category].sort_values('stocks_change')
        records = dict(zip(records['land-cover_2000'], records['stocks_change']))

        data[category] = records

    return data


def get_plot(data):
    categories = list(data.keys())

    lists_labels = [list(value.keys()) for value in data.values()]
    labels = list(set([item for sublist in lists_labels for item in sublist]))

    land_cover_colors = dataset.class_group_colors()

    # Calculate the positions of the bars on the y-axis
    bar_positions = range(len(categories))

    # Create the plot
    fig, ax = plt.subplots()

    for n, label in enumerate(labels):
        values_positive = []
        values_negative = []
        for category in categories[::-1]:
            data_dict = data[category]
            if label in data_dict.keys():
                value = data_dict[label]
                if value > 0:
                    values_positive.append(value)
                    values_negative.append(0)
                else:
                    values_negative.append(value)
                    values_positive.append(0)
            else:
                values_negative.append(0)
                values_positive.append(0)

        if n == 0:
            ax.barh(bar_positions, values_positive, label=label, color=land_cover_colors[label])
            ax.barh(bar_positions, values_negative, color=land_cover_colors[label])

            values_positive_pre = values_positive
            values_negative_pre = values_negative
        elif n == 1:
            ax.barh(bar_positions, values_positive, left=values_positive_pre, label=label,
                    color=land_cover_colors[label])
            ax.barh(bar_positions, values_negative, left=values_negative_pre, color=land_cover_colors[label])

            values_positive_pre = [values_positive_pre[i] + values_positive[i] for i in range(len(values_positive))]
            values_negative_pre = [values_negative_pre[i] + values_negative[i] for i in range(len(values_negative))]
        else:
            ax.barh(bar_positions, values_positive, left=values_positive_pre, label=label,
                    color=land_cover_colors[label])
            ax.barh(bar_positions, values_negative, left=values_negative_pre, color=land_cover_colors[label])

            values_positive_pre = [values_positive_pre[i] + values_positive[i] for i in range(len(values_positive))]
            values_negative_pre = [values_negative_pre[i] + values_negative[i] for i in range(len(values_negative))]

    # Add a dashed line at x = 0
    ax.axvline(0, color='black', linestyle='dashed')

    ## Set the y-axis ticks and labels
    ax.set_yticks(bar_positions)
    ax.set_yticklabels(categories[::-1])
    ax.yaxis.set_ticks_position('none')
    ax.set_ylabel('Land Cover 2018')

    # Set the x-axis label
    ax.set_xlabel('SOC stock change (t C/ha)')

    # Remove the frame
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add a legend
    legend = ax.legend(loc='lower left', bbox_to_anchor=(0.8, 0.5))

    # Set the title of the legend
    legend.set_title('Land Cover 2000')

    # Expand the plot's size to accommodate the legend
    plt.subplots_adjust(right=0.8)

    return plt
