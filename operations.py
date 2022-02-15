import glob
import bbva2pandas as b2p
import pandas as pd


def _extract_operations(path):
    documents = glob.glob(f"{path}/*.pdf")
    dfs = map(lambda x: b2p.Report(x).to_df(), documents)
    return pd.concat(dfs)


def _group_amount_by_year(df):
    df_by_year = df.groupby(df.date.dt.year).sum()
    df_by_year.index = df_by_year.index.to_flat_index()
    df_by_year.index.name = "year"
    return df_by_year.drop(columns="balance").squeeze()


def _group_amount_by_month(df):
    df_by_month = df.groupby([(df.date.dt.year), (df.date.dt.month)]).sum()
    df_by_month.index = df_by_month.index.to_flat_index().map(
        lambda x: f"{str(x[0])[2:]}-{x[1]}"
    )
    df_by_month.index.name = "month"
    return df_by_month.drop(columns="balance").squeeze()


def _group_amount_by_concept(df):
    df_by_concept = df.groupby(df.concept).sum()
    return df_by_concept.drop(columns="balance").squeeze()


def _filter_by_type(df, kind):
    if kind == "incoming":
        return df[df.amount > 0]
    elif kind == "spending":
        return df[df.amount < 0]
    else:
        return df


class Operations:
    def __init__(self, path="."):
        self.operations = _extract_operations(path)
        self.incoming = self.operations.query("amount > 0")
        self.spending = self.operations.query("amount < 0")

    def _concat_groups(self, grouping_func):
        return pd.concat(
            {
                "incoming": grouping_func(self.incoming),
                "spending": grouping_func(self.spending),
                "difference": grouping_func(self.incoming)
                + grouping_func(self.spending),
            },
            axis=1,
        )

    @property
    def group_by_year(self):
        return self._concat_groups(_group_amount_by_year)

    @property
    def group_by_month(self):
        return self._concat_groups(_group_amount_by_month)

    @property
    def group_by_concept(self):
        return self._concat_groups(_group_amount_by_concept)

    @property
    def concepts(self):
        return self.operations.concept.unique()

    def query_by_month(self, month, type):
        operations_by_month = self.operations[
            self.operations.date.dt.strftime("%Y-%m") == month
        ]
        return _filter_by_type(operations_by_month, type)

    def query_by_concept(self, concept, type):
        operations_by_concept = self.operations[self.operations.concept == concept]
        return _filter_by_type(operations_by_concept, type)
