import ipywidgets as widgets
import pandas as pd
import numpy as np
import json

from math import floor
from numbers import Integral
from traitlets import Unicode, Instance, Bool, Integer, Dict, List, Tuple

class _DefaultSettings(object):

    def __init__(self):
        self._grid_options = {
            'fullWidthRows': True,
            'syncColumnCellResize': True,
            'forceFitColumns': True,
            'defaultColumnWidth': 150,
            'rowHeight': 28,
            'enableColumnReorder': False,
            'enableTextSelectionOnCells': True,
            'editable': True,
            'autoEdit': False,
            'explicitInitialization': True
        }
        self._show_toolbar = False
        self._remote_js = False
        self._precision = None  # Defer to pandas.get_option

    def set_grid_option(self, optname, optvalue):
        self._grid_options[optname] = optvalue

    def set_defaults(self, show_toolbar=None, remote_js=None, precision=None, grid_options=None, export_mode=None):
        if show_toolbar is not None:
            self._show_toolbar = show_toolbar
        if remote_js is not None:
            self._remote_js = remote_js
        if precision is not None:
            self._precision = precision
        if grid_options is not None:
            self._grid_options = grid_options

    @property
    def show_toolbar(self):
        return self._show_toolbar

    @property
    def grid_options(self):
        return self._grid_options

    @property
    def remote_js(self):
        return self._remote_js

    @property
    def precision(self):
        return self._precision or pd.get_option('display.precision') - 1

defaults = _DefaultSettings()


def set_defaults(show_toolbar=None, remote_js=None, precision=None, grid_options=None, export_mode=None):
    """
    Set the default qgrid options.  The options that you can set here are the
    same ones that you can pass into ``show_grid``.  See the documentation
    for ``show_grid`` for more information.

    Notes
    -----
    This function will be useful to you if you find yourself
    setting the same options every time you make a call to ``show_grid``.
    Calling this ``set_defaults`` function once sets the options for the
    lifetime of the kernel, so you won't have to include the same options
    every time you call ``show_grid``.

    See Also
    --------
    show_grid :
        The function whose default behavior is changed by ``set_defaults``.
    """
    defaults.set_defaults(show_toolbar, remote_js, precision, grid_options, export_mode)


def set_grid_option(optname, optvalue):
    """
    Set the default value for one of the options that gets passed into the
    SlickGrid constructor.

    Parameters
    ----------
    optname : str
        The name of the option to set.
    optvalue : object
        The new value to set.

    Notes
    -----
    The options you can set here are the same ones
    that you can set via the ``grid_options`` parameter of the ``set_defaults``
    or ``show_grid`` functions.  See the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_ for the full
    list of available options.
    """
    defaults.grid_options[optname] = optvalue


def show_grid(data_frame, show_toolbar=None, remote_js=None, precision=None, grid_options=None, export_mode=None):
    """
    Main entry point for rendering DataFrames as SlickGrids.

    Parameters
    ----------
    grid_options : dict
        Options to use when creating javascript SlickGrid instances.  See the Notes section below for
        more information on the available options, as well as the default options that qgrid uses.
    remote_js : bool
        Whether to load slickgrid.js from a local filesystem or from a
        remote CDN.  Loading from the local filesystem means that SlickGrid
        will function even when not connected to the internet, but grid
        cells created with local filesystem loading will not render
        correctly on external sharing services like NBViewer.
    precision : integer
        The number of digits of precision to display for floating-point
        values.  If unset, we use the value of
        `pandas.get_option('display.precision')`.
    show_toolbar : bool
        Whether to show a toolbar with options for adding/removing rows and
        exporting the widget to a static view.  Adding/removing rows is an
        experimental feature which only works with DataFrames that have an
        integer index.  The export feature is used to generate a copy of the
        grid that will be mostly functional when rendered in nbviewer.jupyter.org
        or when exported to html via the notebook's File menu.
    export_mode : bool
        Whether to display the grid in a notebook or to prepare it to be exported

    Notes
    -----
    By default, the following options get passed into SlickGrid when
    ``show_grid`` is called.  See the `SlickGrid documentation
    <https://github.com/mleibman/SlickGrid/wiki/Grid-Options>`_ for information
    about these options::

        {
            'fullWidthRows': True,
            'syncColumnCellResize': True,
            'forceFitColumns': True,
            'rowHeight': 28,
            'enableColumnReorder': False,
            'enableTextSelectionOnCells': True,
            'editable': True,
            'autoEdit': False
        }

    See Also
    --------
    set_defaults : Permanently set global defaults for `show_grid`.
    set_grid_option : Permanently set individual SlickGrid options.
    """

    if show_toolbar is None:
        show_toolbar = defaults.show_toolbar
    if remote_js is None:
        remote_js = defaults.remote_js
    if precision is None:
        precision = defaults.precision
    if not isinstance(precision, Integral):
        raise TypeError("precision must be int, not %s" % type(precision))
    if grid_options is None:
        grid_options = defaults.grid_options
    else:
        options = defaults.grid_options.copy()
        options.update(grid_options)
        grid_options = options
    if not isinstance(grid_options, dict):
        raise TypeError(
            "grid_options must be dict, not %s" % type(grid_options)
        )

    # create a visualization for the dataframe
    grid = QgridWidget(df=data_frame, precision=precision,
                       grid_options=grid_options,
                       remote_js=remote_js)

    if show_toolbar:
        add_row = widgets.Button(description="Add Row")
        add_row.on_click(grid.add_row)

        rem_row = widgets.Button(description="Remove Row")
        rem_row.on_click(grid.remove_row)

        return widgets.VBox([widgets.HBox([add_row, rem_row]), grid])
    else:
        return grid

@widgets.register('qgrid.QgridWidget')
class QgridWidget(widgets.DOMWidget):
    """"""
    _view_name = Unicode('QgridView').tag(sync=True)
    _model_name = Unicode('QgridModel').tag(sync=True)
    _view_module = Unicode('qgrid').tag(sync=True)
    _model_module = Unicode('qgrid').tag(sync=True)
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    _model_module_version = Unicode('^0.1.0').tag(sync=True)
    value = Unicode('Hello World!').tag(sync=True)

    _df_json = Unicode('', sync=True)
    _filter_query = Unicode('', sync=True)
    _column_types_json = Unicode('', sync=True)
    _primary_key = List()
    _columns = Dict({}, sync=True)
    _index_name = Unicode('')
    _initialized = Bool(False)
    _ignore_df_changed = Bool(False)
    _dirty = Bool(False)
    _multi_index = Bool(False)
    _selected_rows = List()
    _page_size = Integer(100)
    _viewport_range = Tuple(Integer(), Integer(), default_value=(0, 100))
    _df_range = Tuple(Integer(), Integer(), default_value=(0, 100), sync=True)
    _row_count = Integer(0, sync=True)
    _sort_field = Unicode('', sync=True)
    _sort_ascending = Bool(True, sync=True)

    df = Instance(pd.DataFrame)
    unchanged_df = Instance(pd.DataFrame)
    precision = Integer(6, sync=True)
    grid_options = Dict(sync=True)
    remote_js = Bool(False)

    def __init__(self, *args, **kwargs):
        """Initialize all variables before building the table."""
        self._initialized = False
        super(QgridWidget, self).__init__(*args, **kwargs)
        # register a callback for custom messages
        self.on_msg(self._handle_qgrid_msg)
        self._initialized = True
        self._selected_rows = []
        if self.df is not None:
            self.unchanged_df = self.df.copy()
            self._update_table(update_columns=True)

    def _grid_options_default(self):
        return defaults.grid_options

    def _remote_js_default(self):
        return defaults.remote_js

    def _precision_default(self):
        return defaults.precision

    def _df_changed(self):
        """Build the Data Table for the DataFrame."""
        if self._ignore_df_changed or not self._initialized:
            return
        self.unchanged_df = self.df.copy()
        self._update_table(update_columns=True)
        self.send({'type': 'draw_table'})

    def _update_table(self, update_columns=False):
        df = self.df.copy()

        from_index = max(self._viewport_range[0] - self._page_size, 0)
        to_index = max(self._viewport_range[0] + self._page_size, 0)
        self._df_range = (from_index, to_index)

        df = df.iloc[from_index:to_index]

        self._row_count = len(self.df.index)

        if type(df.index) == pd.core.index.MultiIndex:
            self._multi_index = True
        else:
            self._multi_index = False

        self._df_json = df.to_json(
                orient='table',
                date_format='iso',
                double_precision=self.precision,
            )

        if update_columns:
            parsed_json = json.loads(self._df_json)
            columns = {}
            df_schema = parsed_json['schema']
            self._primary_key = df_schema['primaryKey']
            for cur_column in df_schema['fields']:
                columns[cur_column['name']] = cur_column
            self._columns = columns
        else:
            self.send({'type': 'update_data_view'})

    def add_row(self, value=None):
        """Append a row at the end of the dataframe."""
        df = self.df
        if not df.index.is_integer():
            msg = "Cannot add a row to a table with a non-integer index"
            # display(Javascript('alert("%s")' % msg))
            return
        last = df.iloc[-1]
        last.name += 1
        df.loc[last.name] = last.values
        precision = pd.get_option('display.precision') - 1
        row_data = last.to_json(date_format='iso',
                                double_precision=precision)
        msg = json.loads(row_data)
        msg[self._index_name] = str(last.name)
        msg['slick_grid_id'] = str(last.name)
        msg['type'] = 'add_row'
        self._dirty = True
        self.send(msg)

    def remove_row(self, value=None):
        """Remove the current row from the table"""
        if self._multi_index:
            msg = "Cannot remove a row from a table with a multi index"
            # display(Javascript('alert("%s")' % msg))
            return
        self.send({'type': 'remove_row'})

    def _handle_qgrid_msg(self, widget, content, buffers=None):
        """Handle incoming messages from the QGridView"""
        if 'type' not in content:
            return
        if content['type'] == 'remove_row':
            self.df.drop(content['row'], inplace=True)
            self._dirty = True

        elif content['type'] == 'cell_change':
            try:
                self.df.set_value(self.df.index[content['row']],
                                  content['column'], content['value'])
                self._dirty = True
            except ValueError:
                pass
        elif content['type'] == 'selection_change':
            self._selected_rows = content['rows']
        elif content['type'] == 'viewport_changed':
            self._viewport_range = (content['top'], content['bottom'])
            self._update_table()
        elif content['type'] == 'sort_changed':
            self._sort_field = content['sort_field']
            self._sort_ascending = content['sort_ascending']
            if self._sort_field in self._primary_key:
                if len(self._primary_key) == 1:
                    self.df.sort_index(
                        ascending=self._sort_ascending,
                        inplace=True
                    )
                else:
                    self.df.sort_index(
                        level=self._sort_field,
                        ascending=self._sort_ascending,
                        inplace=True
                    )
            else:
                self.df.sort_values(
                    self._sort_field,
                    ascending=self._sort_ascending,
                    inplace=True
                )
            self._update_table()
        elif content['type'] == 'get_column_min_max':
            col_name = content['field']
            col_info = self._columns[col_name]
            if col_name in self._primary_key:
                if len(self._primary_key) > 1:
                    key_index = self._primary_key.index(col_name)
                    col_series = self.df.index[key_index]
                else:
                    col_series = self.df.index
            else:
                col_series = self.df[col_name]
            if col_info['type'] in ['integer', 'number']:
                col_info['slider_max'] = max(col_series)
                col_info['slider_min'] = min(col_series)
                self._columns[col_name] = col_info
                self.send({
                    'type': 'column_min_max_updated',
                    'field': col_name,
                    'col_info': col_info
                })
        elif content['type'] == 'filter_changed':
            col_name = content['field']
            columns = self._columns.copy()
            col_info = columns[col_name]
            col_info['filter_info'] = content['filter_info']
            columns[col_name] = col_info
            filter_query = ""

            def get_prefix(filter_query):
                return ' & ' if len(filter_query) > 0 else ''

            for key, value in columns.items():
                if 'filter_info' in value:
                    filter_info = value['filter_info']
                    prefix = ""
                    if filter_info['type'] == 'slider':
                        if filter_info['min'] is not None:
                            filter_query += "{0}{1} >= {2}".format(
                                get_prefix(filter_query), key, filter_info['min']
                            )
                        if filter_info['max'] is not None:
                            prefix = ' & ' if len(filter_query) > 0 else ''
                            filter_query += "{0}{1} <= {2}".format(
                                get_prefix(filter_query), key, filter_info['max']
                            )
            self._filter_query = filter_query
            self._columns = columns

            self._ignore_df_changed = True
            if filter_query == "":
                self.df = self.unchanged_df.copy()
            else:
                # FYI the following issue happens https://github.com/pandas-dev/pandas/issues/16363
                # with a column with dtype float32.  float64 works fine though.
                self.df = self.unchanged_df.query(filter_query)
            self._update_table()
            self._ignore_df_changed = False


    def get_selected_rows(self):
        """Get the currently selected rows"""
        return self._selected_rows


