# -*- coding: utf-8 -*-
# Project: Antenna Array Configuration
# Author: Nikolai Gaiduchenko
# Copyright: Laboratory of Modelling of Special Computer Systems Architectures / MIPT.
# Verion: 1.2


"""Creates the main window of the application.

This is the main class for the AAC app.
"""
# basic imports
import sys
import numpy as np

# PyQt5 imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMainWindow

# local imports
from . import aac_topology
from .gui import mainwindow_ui
from .gui import table_model
from .gui import table_view_delegate

# define constants
ORGANIZATION_NAME = "MIPT, Laboratory of Design of \
                     Special Computer System Architectures"
APPLICATION_NAME = "Antenna Array Configurator"

class MainWindow(QMainWindow, mainwindow_ui.Ui_MainWindow):
    """Create main window of the application.

    Important (global) attributes:
        settings (:obj:`QSettings`): Application settings, such as window size.
        version (floor): The current version of the app (for logs and saves).
        selected_subarray_number (int): The ID of the subarray chosen to
            draw at start of the app.
        subarray_button_group (:obj:`QButtonGroup`): The group that contains all
            generated subarray buttons.
        view (:obj:`QTableView`): TableView interactive widget.
        topology (:obj:`AACTopology`): antenna array configuration topology
        model (:obj:`TableModel`): a link to `self.view.model` that is
            being set by `MainWindow.set_model` method.

    Unimportant attributes:
        ... lots of PyQt5 buttons and other widgets ...
    """

    # === INIT METHODS ===

    def __init__(self):
        """Initialize `MainWindow` variables and attributes.

        Initialize all the described class attributes. Create new `AACTopology`,
        link it to the application (the topology may be loadded in the future).

        Initialize `TableView`, setup re-implemented painting methods for it.

        Initialize and setup `TableModel`, that interacts with `AACTopology`,
        does data extraction and preprocessing to pass it to `TableView`.

        Set handlers for cell clicking. The cells will be painted as the left
        mouse button is pressed continiously until it is released. For the
        `Tx selection mode` the app remembers the first clicked cell. If the
        first cell was `Tx-selected` before, the cells hovered by the cursor
        will be `Tx-unselected` while the left mouse button is pressed.
        Otherwise, if the first clicked in `Tx selection mode` cell was
        `Tx-unselected`, all the cells hovered by the cursor will be
        `Tx-selected`.

        Generate subarray buttons and spinboxes (subarray forms) on the left
        window panel. The number of subarrays that will be generated is
        specified in `MainWindow.topology.subarrays` variable, that is set up to
        `64` by default. The subarray buttons and spinboxes are added by the
        `add_subarray_form` method.

        Setup `Empty` and `Fault` button methods.
        Setup SLOT-methods for `New`, `Save`, `Load`, `Default`, `Exit` buttons.

        Load previously closed topology from `recentconfig` if exists.

        Sync all subarray counters with topology at the final stage of
        the __init__ initialization.
        """

        super().__init__()
        self.settings = QtCore.QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self.setupUi(self)

        # Control global variables
        self.version = 0.4
        self.selected_subarray_number = 0
        self.subarray_button_group = QtWidgets.QButtonGroup()
        self.grid = self.SubarrayGridLayout
        self.view = self.TableView
        self.topology = aac_topology.AACTopology()
        self.topology.version = self.version

        # Configure TableView to get data from TableModel
        # and to paint cells like in TableViewDelegate
        self.view.setItemDelegate(
            table_view_delegate.TableViewDelegate(self.view))

        self.set_model(view_model=table_model.TableModel,
                       topology=self.topology)

        # Set handlers for cell clicking
        self.view.mouse_pressed = False
        self.view.fst_clk_tx = 1 # first clicked Tx_data
        self.view.mousePressEvent = self._view_mousePressEvent
        self.view.mouseMoveEvent = self._view_mouseMoveEvent
        self.view.mouseReleaseEvent = self._view_mouseReleaseEvent
        self.view.show()

        # Add subarray selection forms in loop to the SubArrayGrid layout
        self.topology.subarrays = 64
        self.spinbox_counters = list()
        for sa in range(1, self.topology.subarrays+1):
            self.add_subarray_form(grid_y=(sa-1) // 4, # OR (sa-1) % sa_bar,
                                   grid_x=(sa-1) % 4,  # OR (sa-1) // sa_bar,
                                   sa=sa,
                                   label=str(sa),
                                   color=self.model.colors[sa])

        # Add Empty button
        self.SubSelectionButton_Empty.subarray = 0
        self.SubSelectionButton_Empty.setStyleSheet(
            "background-color: rgb({i[0]}, {i[1]}, {i[2]})".format(i=self.model.colors[0]))
        self.SubSelectionButton_Empty.clicked.connect(self._subarray_selected)
        self.subarray_button_group.addButton(self.SubSelectionButton_Empty)

        # Add Fault button
        self.SubSelectionButton_Fault.subarray = -1
        self.SubSelectionButton_Fault.setStyleSheet(
            "background-color: rgb({i[0]}, {i[1]}, {i[2]})".format(i=self.model.colors[0]))
        self.SubSelectionButton_Fault.clicked.connect(self._subarray_selected)
        self.subarray_button_group.addButton(self.SubSelectionButton_Fault)

        # Initialize Tx_data buttons SLOTS
        self.SelectAllButton.pressed.connect(self._select_all_button_clicked)
        self.ClearAllButton.pressed.connect(self._clear_all_button_clicked)

        # Initialize main_panel buttons SLOTS
        self.NewButton.clicked.connect(self._new_button_clicked)
        self.DefaultButton.clicked.connect(self._default_button_clicked)
        self.SaveButton.clicked.connect(self._save_button_clicked)
        self.LoadButton.clicked.connect(self._load_button_clicked)
        self.ExitButton.clicked.connect(self._exit_button_clicked)

        # Setup Settings elements groupbox SLOTS
        self.GridCheckbox.stateChanged.connect(self.show_grid)
        self.ZoomPlusButton.clicked.connect(self.view_zoom_in)
        self.ZoomMinusButton.clicked.connect(self.view_zoom_out)
        self.ZoomRestoreButton.clicked.connect(self.view_zoom_restore)

        # load recent data
        self.load_data(self.topology.fpath_recent)

        # Read window geometry and main settings
        self.read_settings()

        # display actual statistics for the loaded data
        self.sync_counters()                # Display actual information loaded from topology
        self.sync_topology()                # Set initial computed info from counters
        self.update_subarray_counters()     # Count missing information for other counters
        self.spinBox_2_1.setValue(self.model.columnCount())
        self.spinBox_2_2.setValue(self.model.rowCount())
        print(self.topology)

    def add_subarray_form(self, grid_y, grid_x, label='', sa=0, color=(255, 255, 255)):
        """Add subarray form layout to the `Rx Groupbox`.

        The form contains a `QPushButton` with the subarray number and
        `QSpinBox` for counting how many modules (QTableView cells) were marked
        with that subarray number.

        The `subarray_form` object is a `QWidget` with a `QPushButton` and
        `QSpinBox` inside aligned with QHBoxLayout. Created `QPushButton` is
        added to the previously initialized `MainWindow.subarray_button_group`
        group. Created `QSpinBox` is added to `MainWindow.spinbox_counters` list
        for convenient work and updating in the future. Created `subarray_form`
        is added as a `QWidget` to `MainWindow.grid` object.

        Args:
            grid_y (int): The `y` grid index to insert the form into.
            grid_x (int): The `x` grid index to insert the form into.
            label (str): The text to be printed on the subarray button.
            sa (int): The subarray number.
            color (:obj:`tuple`(int R, int G, int B)): The tuple that contains
                R, G, B integer values (each value from 0 to 255) to paint the
                subarray button into.
        """

        # Setup fonts
        font = QtGui.QFont()
        font.setPointSize(11)

        spinbox_font = QtGui.QFont()
        spinbox_font.setPointSize(9)

        # Create new subarray_form
        subarray_form = QtWidgets.QWidget()
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                            QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(subarray_form.sizePolicy().hasHeightForWidth())
        subarray_form.setSizePolicy(size_policy)

        # Create subarray_form horizontal layout
        subarray_form_layout = QtWidgets.QHBoxLayout(subarray_form)
        subarray_form_layout.setContentsMargins(3, 3, 3, 3)
        subarray_form_layout.setSpacing(5)

        # Create PushButton and add it to subarray_form_layout
        subarray_button = QtWidgets.QPushButton(subarray_form)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                            QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(subarray_button.sizePolicy().hasHeightForWidth())
        subarray_button.setSizePolicy(size_policy)
        subarray_button.setMinimumSize(QtCore.QSize(21, 25))
        subarray_button.setMaximumSize(QtCore.QSize(25, 30))
        subarray_button.setFont(font)
        subarray_button.setCheckable(True)
        subarray_form_layout.addWidget(subarray_button, 0,
                                       QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        # Set button text, subarray number and background color
        subarray_button.subarray = sa
        subarray_button.setText(label)
        subarray_button.setStyleSheet(
            "background-color: rgb({i[0]}, {i[1]}, {i[2]})".format(i=color))
        # Connect QPushButton of the subarray to MainWindow click slot
        subarray_button.clicked.connect(self._subarray_selected)
        # Add the subarray QPushButton to the subarray_button_group
        self.subarray_button_group.addButton(subarray_button)

        # Create SpinBox and add it to subarray_form_layout
        subarray_spinbox = QtWidgets.QSpinBox(subarray_form)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(3)
        size_policy.setVerticalStretch(3)
        size_policy.setHeightForWidth(subarray_spinbox.sizePolicy().hasHeightForWidth())
        subarray_spinbox.setSizePolicy(size_policy)
        subarray_spinbox.setFocusPolicy(QtCore.Qt.NoFocus)
        subarray_spinbox.setMinimumSize(QtCore.QSize(20, 25))
        subarray_spinbox.setAcceptDrops(False)
        subarray_spinbox.setAlignment(QtCore.Qt.AlignCenter)
        subarray_spinbox.setReadOnly(True)
        subarray_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        subarray_spinbox.setMaximum(999999999)
        subarray_spinbox.setFont(spinbox_font)
        subarray_form_layout.addWidget(subarray_spinbox, 0,
                                       QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.spinbox_counters.append(subarray_spinbox)

        # Add created `subarray_form` to the given `grid` layout
        self.grid.addWidget(subarray_form, grid_y, grid_x, 1, 1)


    # === TableModel INTERACTION METHODS ===

    def set_model(self, view_model=table_model.TableModel, topology=None):
        """Setup TableView to display TableModel contents.

        Note:
            If the `topology` argument is `None`, the new topology with empty
            data will be created and assigned. Also this method calls the
            `resize_model` method after setting the model to fit all the new
            loaded data.

        Args:
            view_model (:obj:`TableModel`): The re-implemented class of
                `QAbstractTableModel`, that provides interaction methods with
                the topology data.
            topology (:obj:AACTopology, optional): The `AACTopology` that will
                be set to interact with via `view_model`.

        """
        self.view.setModel(view_model(topology=topology))
        self.model = self.view.model()
        self.resize_model()

    def resize_model(self):
        """Resize table elements to MxN px

            Set the column width and row height for every column and row in
            TableView. Also set `Fixed` section resize mode to table headers,
            so the table become unstretchable.

            Note:
                This method also is used to zoom the table. See the docs for
                `MainWindow.view_zoom_in` and `MainWindow.view_zoom_out`.
        """

        for i in range(self.view.model().rowCount()):
            self.view.setRowHeight(i, self.model.cell_size[0])
        for i in range(self.view.model().columnCount()):
            self.view.setColumnWidth(i, self.model.cell_size[1])
        self.view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.view.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)


    # === MOUSE EVENT HANDLERS ===

    def _view_mousePressEvent(self, event):
        """Handle left mouse button is pressed to start painting cells.

        The method handles mousePressEvent for MainWindow.view that is being
        emitted, when the mouse button is pressed. If user presses left mouse
        button over tha MainWindow.view, this method activates the painting
        process, which will last until the left mouse button is released.

        Note:
            For the `Tx selection mode` the app remembers the first clicked
            cell. If the first cell was `Tx-selected` before, the cells hovered
            by the cursor will be `Tx-unselected` while the left mouse button is
            pressed. Otherwise, if the first clicked in `Tx selection mode` cell
            was `Tx-unselected`, all the cells hovered by the cursor will be
            `Tx-selected`.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.view.selected_index = self.view.indexAt(event.pos())
            if self.view.selected_index.isValid():
                self.view.mouse_pressed = True

                fst_row = self.view.selected_index.row()
                fst_col = self.view.selected_index.column()
                self.view.fst_clk_tx = self.topology.Tx_data[fst_row, fst_col]

                self._view_click_cell(self.view.selected_index)


    def _view_mouseMoveEvent(self, event):
        """Handle mouse movements to paint cells in `MainWindow.view`."""
        if self.view.mouse_pressed:
            index = self.view.indexAt(event.pos())
            if index.isValid() and self.view.selected_index != index:
                self.view.selected_index = index
                self._view_click_cell(index)

    def _view_mouseReleaseEvent(self, event):
        """Handle the event that the left mouse button is released.)

        Note:
            All subarray counters are updated only at the end of drawing,
            at this method.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.view.mouse_pressed = False
        self.update_subarray_counters()


    # === TableView METHODS ===

    def _view_click_cell(self, clicked_idx):
        """Update topology `clicked_idx` cell data through `TableModel`.

        This is a SLOT for cells from `TableView` to handle situations when the
        cell gets clicked. The slot updates `MainWindow.topology.Rx_data` and
        `Tx_data` arrays and force-repaint clicked `TableView` cell to get
        instant visual update.

        Args:
            clicked_idx (:obj:`QModelIndex`): The index of the clicked cell.
        """
        if not clicked_idx.isValid():
            return

        row = clicked_idx.row()
        col = clicked_idx.column()

        # Set new data in topology via self.model method and redraw table cell
        if self.SelectCellButton.isChecked():
            # Switch cell as Tx or back if it's data equals the data of the
            # first clicked cell when the mouse was pressed.
            tx_flag = self.topology.Tx_data[row, col]
            if tx_flag == self.view.fst_clk_tx:
                self.topology.set_Tx_data(row=row, col=col, data=tx_flag ^ 1)
        else:
            self.topology.set_Rx_data(row=row, col=col, data=self.selected_subarray_number)

        self.model.update_index(row, col)

    def view_zoom_in(self):
        """Increment cell size in QTableView by 3 px."""
        self.model.change_cell_size([3, 3])
        self.resize_model()

    def view_zoom_out(self):
        """Decrement cell size in QTableView by 3 px."""
        self.model.change_cell_size([-3, -3])
        self.resize_model()

    def view_zoom_restore(self):
        """Restore cell size in QTableView to default."""
        self.model.set_cell_size(set_default=True)
        self.resize_model()

    def show_grid(self):
        """Toggle show grid."""
        self.view.setShowGrid(self.GridCheckbox.isChecked())

    def _subarray_selected(self):
        """Get the subarray number of the pressed button and unpress others.

        This is a SLOT for subarray selection buttons in subarray_forms
        to handle situations when the button gets clicked. It unpresses
        all other subarray buttons and sets selected_subarray_number.

        The other buttons unpress automatically, because all the subarray
        buttons were added to `MainWindow.subarray_button_group` during the
        initialization.

        The `Select cell` Tx-selection mode button will be unpressed to be able
        to draw new subarrays immediately.
        """

        self.selected_subarray_number = self.sender().subarray
        self.SelectCellButton.setChecked(False)

    # === TOPOLOGY AND COUNTERS SYNCHRONISATION ===

    def update_subarray_counters(self):
        """Update subarray counters after TableView interaction.

        The main difference between this method and `MainWindow.sync_counters`
        is that this method is called to re-compute all the neccessary
        information right after the topology data was changed to display actual
        data. This method affects only counters being affected by painting cells
        in `MainWindow.view` and it is made as simple and fast as it can be
        done to paint cells quickly, so it is more 'lightweight' update.

        The `Mainwindow.sync_counters` instead updates ALL of the subarray
        counters with the information from the topology directly and it is more
        slower and more general.
        """

        unique, counts = np.unique(self.topology.Rx_data, return_counts=True)
        for sa in range(self.topology.subarrays):
            self.spinbox_counters[sa].setValue(0)

        for sa, num in zip(unique, counts):
            if sa == 0: # empty cell
                pass
            elif sa == -1: # fault cell
                pass
            else:
                self.spinbox_counters[sa-1].setValue(num)

        # Set general spinboxes
        data_shape = self.topology.shape()
        self.topology.module_width_elem = self.spinBox_1_1.value()
        self.topology.module_height_elem = self.spinBox_1_2.value()
        self.spinBox_3_1.setValue(data_shape[1])
        self.spinBox_3_2.setValue(data_shape[0])
        self.spinBox_4_1.setValue(data_shape[1] * self.topology.module_width_elem)
        self.spinBox_4_2.setValue(data_shape[0] * self.topology.module_height_elem)

        # Set Total spinboxes
        subarrays_and_fault = np.delete(counts, np.argwhere(unique == 0))
        subarrays_only = np.delete(subarrays_and_fault, np.argwhere(counts == -1))

        self.topology.Nmodules = sum(subarrays_and_fault)
        self.topology.Nelements = self.topology.Nmodules \
                                  * self.topology.module_width_elem \
                                  * self.topology.module_height_elem
        self.topology.Nsubarrays = len(subarrays_only)

        self.spinBox_Nelements.setValue(self.topology.Nelements)
        self.spinBox_Nmodules.setValue(self.topology.Nmodules)
        self.spinBox_Nsubarrays.setValue(self.topology.Nsubarrays)

        # Set Tx selected cell counter
        self.topology.Tx_cells = np.sum(self.topology.Tx_submatrix)
        self.spinBox_selectCell.setValue(self.topology.Tx_cells)

    def sync_topology(self):
        """Sync topology variables with values from GUI elements."""
        self.topology.version = self.version
        self.topology.module_width_elem = self.spinBox_1_1.value()
        self.topology.module_height_elem = self.spinBox_1_2.value()
        self.topology.Rx_grid_width_elem = self.spinBox_4_1.value()
        self.topology.Rx_grid_height_elem = self.spinBox_4_2.value()

        # Get the actual submatrix from the matrix_with_rx_submatrix_shapes Tx_submatrix
        tx_sub = self.topology.submatrix(self.topology.Tx_submatrix)
        self.topology.Tx_grid_width_elem = self.topology.submatrix(tx_sub).shape[1] * \
                                           self.topology.module_width_elem
        self.topology.Tx_grid_height_elem = self.topology.submatrix(tx_sub).shape[0] * \
                                            self.topology.module_width_elem
        self.topology.Tx_X_origin = -1
        self.topology.Tx_Y_origin = -1
        self.topology.X_stepping = self.spinBox_5_1.value()
        self.topology.Y_stepping = self.spinBox_5_2.value()
        self.topology.triangle_grid_flag = 1 if self.TriangleGridCheckbox.isChecked() else 0
        self.topology.taylor_wnd_function_flag = (
            1 if self.TaylorWndFunctionCheckbox.isChecked() else 0)
        self.topology.antenna_element_type = self.ElementPatternComboBox.currentIndex() + 1
        self.topology.gain_dB = self.spinBox_GdB.value()
        self.topology.gain_error = self.spinBox_gain.value()
        self.topology.phase_error = self.spinBox_phase.value()
        self.topology.Nmodules = self.spinBox_Nmodules.value()
        self.topology.Nelements = self.spinBox_Nelements.value()
        self.topology.Nsubarrays = self.spinBox_Nsubarrays.value()
        self.topology.Tx_cells = self.spinBox_selectCell.value()

    def sync_counters(self):
        """Sync all GUI counters with actual values from topology variables."""
        data_shape = self.topology.shape()
        self.spinBox_1_1.setValue(self.topology.module_width_elem)
        self.spinBox_1_2.setValue(self.topology.module_height_elem)
        self.spinBox_2_1.setValue(self.model.columnCount())
        self.spinBox_2_2.setValue(self.model.rowCount())
        self.spinBox_3_1.setValue(data_shape[1])
        self.spinBox_3_2.setValue(data_shape[0])
        self.spinBox_4_1.setValue(self.topology.Rx_grid_width_elem)
        self.spinBox_4_2.setValue(self.topology.Rx_grid_height_elem)
        self.spinBox_5_1.setValue(self.topology.X_stepping)
        self.spinBox_5_2.setValue(self.topology.Y_stepping)

        self.TriangleGridCheckbox.setChecked(self.topology.triangle_grid_flag)
        self.TaylorWndFunctionCheckbox.setChecked(self.topology.taylor_wnd_function_flag)
        self.ElementPatternComboBox.setCurrentIndex(self.topology.antenna_element_type - 1)

        self.spinBox_GdB.setValue(self.topology.gain_dB)
        self.spinBox_gain.setValue(self.topology.gain_error)
        self.spinBox_phase.setValue(self.topology.phase_error)

        self.spinBox_Nelements.setValue(self.topology.Nelements)
        self.spinBox_Nmodules.setValue(self.topology.Nmodules)
        self.spinBox_Nsubarrays.setValue(self.topology.Nsubarrays)
        self.spinBox_selectCell.setValue(self.topology.Tx_cells)


    # === QPushButton SLOTS ===

    def _select_all_button_clicked(self):
        """Set all the Rx_data marked cells as Tx_data marked too."""
        self.view.setUpdatesEnabled(False)
        # if Rx[a] != 0 then set Tx[a] = 1 else set Tx[a] = 0
        self.topology.set_Tx_data(np.ones_like(self.topology.Rx_data))
        self.update_subarray_counters()
        self.view.reset()
        self.view.setUpdatesEnabled(True)

    def _clear_all_button_clicked(self):
        """Clear the Tx_data matrix."""
        self.view.setUpdatesEnabled(False)
        self.topology.set_Tx_data(np.zeros_like(self.topology.Tx_data))
        self.update_subarray_counters()
        self.view.reset()
        self.view.setUpdatesEnabled(True)

    def _new_button_clicked(self):
        """Create and load empty table with the size from the spinboxes."""
        self.view.setUpdatesEnabled(False)

        # Get the new table shapes from spinboxes
        self.topology.def_shapes = [self.spinBox_2_2.value(),
                                    self.spinBox_2_1.value()]
        # Create and setup new topology with empty Rx and Tx data
        self.topology.set_Rx_data()
        self.topology.set_Tx_data()
        self.set_model(view_model=table_model.TableModel,
                       topology=self.topology)
        # Update all displayable info
        self.update_subarray_counters()
        self.view.reset()
        self.view.setUpdatesEnabled(True)

    def _default_button_clicked(self):
        """Load default config table (saved as "data/defaultconfig.txt")."""
        self.load_data(self.topology.fpath_default)

    def _save_button_clicked(self):
        """Choose a filename, then save the entire topology and picture."""
        fpath_save = QFileDialog.getSaveFileName(self,
                                                 caption='Save AAC',
                                                 directory=self.topology.fpath_save,
                                                 filter='*.txt')[0]

        # If cancel button wasn't pressed in QFileDialog
        if fpath_save != '':
            self.save_data(fpath_save)
            self.save_picture(fpath_save[:-4])

    def _load_button_clicked(self):
        """Choose a file, then load it's topology from selected config file."""
        fpath_load = QFileDialog.getOpenFileName(self,
                                                 caption='Load AAC',
                                                 directory=self.topology.fpath_save,
                                                 filter='*.txt')[0]

        # If cancel button wasn't pressed in QFileDialog
        if fpath_load != '':
            self.load_data(fpath_load)

    def _exit_button_clicked(self):
        """Handle exit button clicked event and then exit from the app."""
        self._exit_handler()
        sys.exit(0)


    # == DATA & SETTINGS SAVING / LOADING ===

    def save_data(self, fpath=''):
        """Sync the topology to the actual state and them save it to `fpath`."""
        # Get actual data from all the spinBoxes and other GUI elements
        self.sync_topology()
        self.topology.save(fpath)

    def save_picture(self, fpath=''):
        """Save MainWindow.view data as PNG picture to the `fpath` arg given."""
        fpath += '.png'
        pixmap = QtGui.QPixmap(self.model.size())
        self.view.render(pixmap)
        pixmap.save(fpath)

    def load_data(self, fname=''):
        """Load topology from 'fname' argument and then display it."""
        # Freeze TableView for a sec to load data
        self.view.setUpdatesEnabled(False)

        # Load topology from the filename given and sync all spinbox counters
        self.topology.load(fname)
        self.sync_counters()

        # Setup TableModel to display loaded data from new topology
        self.set_model(view_model=table_model.TableModel,
                       topology=self.topology)
        self.update_subarray_counters()
        self.view.setUpdatesEnabled(True)

    def read_settings(self):
        """Read previously saved settings and restore window geometry."""
        self.settings.beginGroup("MainWindow")
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))
        self.restoreState(self.settings.value("window_state", QtCore.QByteArray()))

        # Restore saved cell size
        cell_size_sets = self.settings.value("cell_size", QtCore.QByteArray())
        self.model.set_cell_size(cell_size_sets)
        self.resize_model()

        # Restore grid setting
        grid_enabled = self.settings.value("grid_enabled", QtCore.QByteArray())
        if isinstance(grid_enabled, bool):
            self.GridCheckbox.setChecked(grid_enabled)

        self.settings.endGroup()

    def write_settings(self):
        """Write current window geometry settings."""
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        self.settings.setValue("cell_size", self.model.cell_size)
        self.settings.setValue("grid_enabled", self.GridCheckbox.isChecked())
        self.settings.endGroup()


    # === EXIT HANDLERS ===

    def closeEvent(self, event):
        """Handle window close events when the exit button isn't pressed.

        Re-implements default PyQt5 `closeEvent` for `QMainWindow`. The
        difference is that this class saves all the data before exit to
        the `recentconfig` via `_exit_handler` method.
        """
        self._exit_handler()
        event.accept() # let the window close

    def _exit_handler(self):
        """Save everything to recentconfig.txt and QSettings before exit."""
        self.update_subarray_counters()
        self.sync_topology()
        self.save_data(self.topology.fpath_recent)
        self.write_settings()
