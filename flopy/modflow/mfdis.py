"""
mfdis module.  Contains the ModflowDis class. Note that the user can access
the ModflowDis class as `flopy.modflow.ModflowDis`.

Additional information for this MODFLOW package can be found at the `Online
MODFLOW Guide
<http://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/index.html?dis.htm>`_.

"""

import sys
import numpy as np
from flopy.mbase import Package
from flopy.utils import util_2d,util_3d,reference

class ModflowDis(Package):
    """
    MODFLOW Discretization Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.Modflow`) to which
        this package will be added.
    nlay : int
        Number of model layers (the default is 1).
    nrow : int
        Number of model rows (the default is 2).
    ncol : int
        Number of model columns (the default is 2).
    nper : int
        Number of model stress periods (the default is 1).
    delr : float or array of floats (ncol), optional
        An array of spacings along a row (the default is 1.0).
    delc : float or array of floats (nrow), optional
        An array of spacings along a column (the default is 0.0).
    laycbd : int or array of ints (nlay), optional
        An array of flags indicating whether or not a layer has a Quasi-3D
        confining bed below it. 0 indicates no confining bed, and not zero
        indicates a confining bed. LAYCBD for the bottom layer must be 0. (the
        default is 1)
    top : float or array of floats (nrow, ncol), optional
        An array of the top elevation of layer 1. For the common situation in
        which the top layer represents a water-table aquifer, it may be
        reasonable to set Top equal to land-surface elevation (the default is
        1.0)
    botm : float or array of floats (nlay, nrow, ncol), optional
        An array of the bottom elevation for each model cell (the default is
        0.)
    perlen : float or array of floats (nper)
        An array of the stress period lengths.
    nstp : int or array of ints (nper)
        Number of time steps in each stress period (default is 1).
    tsmult : float or array of floats (nper)
        Time step multiplier (default is 1.0).
    steady : boolean or array of boolean (nper)
        true or False indicating whether or not stress period is steady state
        (default is True).
    itmuni : int
        Time units, default is days (4)
    lenuni : int
        Length units, default is meters (2)
    extension : string
        Filename extension (default is 'dis')
    unitnumber : int
        File unit number (default is 11).


    Attributes
    ----------
    heading : str
        Text string written to top of package input file.

    Methods
    -------

    See Also
    --------

    Notes
    -----

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modflow.Modflow()
    >>> dis = flopy.modflow.ModflowDis(m)

    """

    def __init__(self, model, nlay=1, nrow=2, ncol=2, nper=1, delr=1.0,
                 delc=1.0, laycbd=0, top=1, botm=0, perlen=1, nstp=1,
                 tsmult=1, steady=True, itmuni=4, lenuni=2, extension='dis',
                 unitnumber=11,start_datetime=None,xul=None,yul=None,rotation=0.0):

        # Call ancestor's init to set self.parent, extension, name and unit
        # number
        Package.__init__(self, model, extension, 'DIS', unitnumber)
        self.url = 'dis.htm'
        self.nrow = nrow
        self.ncol = ncol
        self.nlay = nlay
        self.nper = nper

        # Set values of all parameters
        self.heading = '# Discretization file for MODFLOW, generated by Flopy.'
        self.laycbd = util_2d(model, (self.nlay,), np.int, laycbd,
                              name='laycbd')
        self.laycbd[-1] = 0  # bottom layer must be zero
        self.delr = util_2d(model, (self.ncol,), np.float32, delr, name='delr',
                            locat=self.unit_number[0])
        self.delc = util_2d(model,(self.nrow,), np.float32, delc, name='delc',
                            locat=self.unit_number[0])
        self.top = util_2d(model, (self.nrow,self.ncol), np.float32,
                           top,name='model_top', locat=self.unit_number[0])
        self.botm = util_3d(model, (self.nlay+sum(self.laycbd),
                                    self.nrow,self.ncol), np.float32, botm,
                                    'botm', locat=self.unit_number[0])
        self.perlen = util_2d(model, (self.nper,), np.float32, perlen,
                              name='perlen')
        self.nstp = util_2d(model, (self.nper,), np.int, nstp, name='nstp')
        self.tsmult = util_2d(model, (self.nper,), np.float32, tsmult,
                              name='tsmult')
        self.steady = util_2d(model, (self.nper,), np.bool,
                              steady,name='steady')
        self.itmuni = int(itmuni)
        self.lenuni = int(lenuni)
        self.parent.add_package(self)
        self.itmuni_dict = {0: "undefined", 1: "seconds", 2: "minutes",
                            3: "hours", 4: "days", 5: "years"}

        self.sr = reference.SpatialReference(self.delr, self.delc, self.lenuni, xul=xul,
                                             yul=yul, rotation_degrees=rotation)
        self.tr = reference.TemporalReference(self.perlen, self.steady, self.nstp, self.tsmult,
                                              self.itmuni, start_datetime=start_datetime)

    def checklayerthickness(self):
        """
        Check layer thickness.

        """
        return (self.thickness > 0).all()

    def get_cell_volumes(self):
        """
        Get an array of cell volumes.

        Returns
        -------
        vol : array of floats (nlay, nrow, ncol)

        """
        vol = np.empty((self.nlay, self.nrow, self.ncol))
        for l in range(self.nlay):
            vol[l, :, :] *= self.thickness.array[l]
        for r in range(self.nrow):
            vol[:, r, :] *= self.delc[r]
        for c in range(self.ncol):
            vol[:, :, c] *= self.delr[c]
        return vol

    def get_node_coordinates(self):
        """
        Get y, x, and z cell centroids.

        Returns
        -------
        y : list of cell y-centroids

        x : list of cell x-centroids

        z : array of floats (nlay, nrow, ncol)
        """
        # In row direction
        y = np.empty((self.nrow))
        for r in range(self.nrow):
            if (r == 0):
                y[r] = self.delc[r] / 2.
            else:
                y[r] = y[r - 1] + (self.delc[r] + self.delc[r - 1]) / 2.
        # Invert y to convert to a cartesian coordiante system
        y = y[::-1]
        # In column direction
        x = np.empty((self.ncol))
        for c in range(self.ncol):
            if (c == 0):
                x[c] = self.delr[c] / 2.
            else:
                x[c] = x[c - 1] + (self.delr[c] + self.delr[c - 1]) / 2.
        # In layer direction
        z = np.empty((self.nlay, self.nrow, self.ncol))
        for l in range(self.nlay):
            if (l == 0):
                z[l, :, :] = (self.top[:, :] + self.botm[l, :, :]) / 2.
            else:
                z[l, :, :] = (self.botm[l - 1, :, :] + self.botm[l, :, :]) / 2.
        return y, x, z

    def get_lrc(self, nodes):
        """
        Get layer, row, column from a list of MODFLOW node numbers.

        Returns
        -------
        v : list of tuples containing the layer (k), row (i), 
            and column (j) for each node in the input list
        """
        if not isinstance( nodes, list ):
            nodes = [nodes]
        nrc = self.nrow * self.ncol
        v = []
        for node in nodes:
            k  = int( node / nrc )
            if ( k * nrc ) < node:
                k += 1
            ij = int( node - ( k - 1 ) * nrc )
            i  = int( ij / self.ncol )
            if ( i * self.ncol ) < ij:
                i += 1
            j = ij - ( i - 1 ) * self.ncol
            v.append((k, i, j))
        return v
        
    def get_node(self, lrc_list):
        """
        Get node number from a list of MODFLOW layer, row, column tuples.

        Returns
        -------
        v : list of MODFLOW nodes for each layer (k), row (i), 
            and column (j) tuple in the input list
        """
        if not isinstance( lrc_list, list ):
            lrc_list = [lrc_list]
        nrc = self.nrow * self.ncol
        v = []
        for [k,i,j] in lrc_list:
            node = int( ( ( k - 1 ) * nrc ) + ( ( i - 1 ) * self.ncol ) + j  )
            v.append(node)
        return v

    def read_from_cnf(self, cnf_file_name, n_per_line = 0):
        """
        Read discretization informatio from an MT3D configuration file.

        """

        def getn(ii, jj):
            if (jj == 0):
                n = 1
            else:
                n = int(ii / jj)
                if (ii % jj != 0):
                    n = n + 1

            return n

        try:
            f_cnf = open(cnf_file_name, 'r')

            # nlay, nrow, ncol
            line = f_cnf.readline()
            s = line.split()
            cnf_nlay = int(s[0])
            cnf_nrow = int(s[1])
            cnf_ncol = int(s[2])

            # ncol column widths delr[c]
            line = ''
            for dummy in range(getn(cnf_ncol, n_per_line)):
                line = line + f_cnf.readline()
            cnf_delr = [float(s) for s in line.split()]

            # nrow row widths delc[r]
            line = ''
            for dummy in range(getn(cnf_nrow, n_per_line)):
                line = line + f_cnf.readline()
            cnf_delc = [float(s) for s in line.split()]

            # nrow * ncol htop[r, c]
            line = ''
            for dummy in range(getn(cnf_nrow * cnf_ncol, n_per_line)):
                line = line + f_cnf.readline()
            cnf_top = [float(s) for s in line.split()]
            cnf_top = np.reshape(cnf_top, (cnf_nrow, cnf_ncol))

            # nlay * nrow * ncol layer thickness dz[l, r, c]
            line = ''
            for dummy in range(getn(cnf_nlay * cnf_nrow * cnf_ncol, n_per_line)):
                line = line + f_cnf.readline()
            cnf_dz = [float(s) for s in line.split()]
            cnf_dz = np.reshape(cnf_dz, (cnf_nlay, cnf_nrow, cnf_ncol))

            # cinact, cdry, not used here so commented
            '''line = f_cnf.readline()
            s = line.split()
            cinact = float(s[0])
            cdry = float(s[1])'''

            f_cnf.close()
        finally:
            self.nlay = cnf_nlay
            self.nrow = cnf_nrow
            self.ncol = cnf_ncol

            self.delr = util_2d(model, (self.ncol,), np.float32, cnf_delr, 
                                name='delr', locat=self.unit_number[0])
            self.delc = util_2d(model, (self.nrow,), np.float32, cnf_delc, 
                                name='delc', locat=self.unit_number[0])
            self.top = util_2d(model, (self.nrow,self.ncol), np.float32,
                                       cnf_top, name='model_top', 
                                       locat = self.unit_number[0])

            cnf_botm = np.empty((self.nlay + sum(self.laycbd),self.nrow, 
                                 self.ncol))

            # First model layer
            cnf_botm[0:, :, :] = cnf_top - cnf_dz[0, :, :]
            # All other layers
            for l in range(1, self.nlay):
                cnf_botm[l, :, :] = cnf_botm[l - 1, :, :] - cnf_dz[l, :, :]

            self.botm = util_3d(model, (self.nlay + sum(self.laycbd),
                                        self.nrow, self.ncol), np.float32,
                                        cnf_botm, 'botm', 
                                        locat = self.unit_number[0])

    def gettop(self):
        """
        Get the top array.

        Returns
        -------
        top : array of floats (nrow, ncol)
        """
        return self.top.array

    def getbotm(self, k=None):
        """
        Get the bottom array.

        Returns
        -------
        botm : array of floats (nlay, nrow, ncol), or

        botm : array of floats (nrow, ncol) if k is not none
        """
        if k is None:
            return self.botm.array
        else:
            return self.botm.array[k,:,:]

    @property
    def thickness(self):
        """
        Get a util_3d array of cell thicknesses.

        Returns
        -------
        thickness : util3d array of floats (nlay, nrow, ncol)

        """
        thk = []
        thk.append(self.top - self.botm[0])
        for k in range(1,self.nlay):
            thk.append(self.botm[k-1] - self.botm[k])
        self.__thickness = util_3d(self.parent, (self.nlay, self.nrow,
                                                 self.ncol), np.float32, thk,
                                                 name='thickness')
        return self.__thickness

    def write_file(self):
        """
        Write the file.

        """
        # Open file for writing
        f_dis = open(self.fn_path, 'w')
        # Item 0: heading        
        f_dis.write('{0:s}\n'.format(self.heading))
        # Item 1: NLAY, NROW, NCOL, NPER, ITMUNI, LENUNI        
        f_dis.write('{0:10d}{1:10d}{2:10d}{3:10d}{4:10d}{5:10d}\n'\
            .format(self.nlay, self.nrow, self.ncol, self.nper, self.itmuni,
                    self.lenuni))
        # Item 2: LAYCBD
        for l in range(0, self.nlay):            
            f_dis.write('{0:3d}'.format(self.laycbd[l]))
        f_dis.write('\n')
        # Item 3: DELR
        f_dis.write(self.delr.get_file_entry())
        # Item 4: DELC       
        f_dis.write(self.delc.get_file_entry())
        # Item 5: Top(NCOL, NROW)
        f_dis.write(self.top.get_file_entry())
        # Item 5: BOTM(NCOL, NROW)        
        f_dis.write(self.botm.get_file_entry())

        # Item 6: NPER, NSTP, TSMULT, Ss/tr
        for t in range(self.nper):           
            f_dis.write('{0:14f}{1:14d}{2:10f} '.format(self.perlen[t],
                                                        self.nstp[t],
                                                        self.tsmult[t]))
            if self.steady[t]:                
                f_dis.write(' {0:3s}\n'.format('SS'))
            else:                
                f_dis.write(' {0:3s}\n'.format('TR'))
        f_dis.close()

    @staticmethod
    def load(f, model, ext_unit_dict=None):
        """
        Load an existing package.

        Parameters
        ----------
        f : filename or file handle
            File to load.
        model : model object
            The model object (of type :class:`flopy.modflow.mf.Modflow`) to
            which this package will be added.
        ext_unit_dict : dictionary, optional
            If the arrays in the file are specified using EXTERNAL,
            or older style array control records, then `f` should be a file
            handle.  In this case ext_unit_dict is required, which can be
            constructed using the function
            :class:`flopy.utils.mfreadnam.parsenamefile`.

        Returns
        -------
        dis : ModflowDis object
            ModflowDis object.

        Examples
        --------

        >>> import flopy
        >>> m = flopy.modflow.Modflow()
        >>> dis = flopy.modflow.ModflowDis.load('test.dis', m)

        """

        if model.verbose:
            sys.stdout.write('loading dis package file...\n')

        if not hasattr(f, 'read'):
            filename = f
            f = open(filename, 'r')
        # dataset 0 -- header
        while True:
            line = f.readline()
            if line[0] != '#':
                break
        # dataset 1
        nlay, nrow, ncol, nper, itmuni, lenuni = line.strip().split()[0:6]
        nlay = int(nlay)
        nrow = int(nrow)
        ncol = int(ncol)
        nper = int(nper)
        itmuni = int(itmuni)
        lenuni = int(lenuni)
        # dataset 2 -- laycbd
        if model.verbose:
            print('   Loading dis package with:\n      ' + \
                  '{0} layers, {1} rows, {2} columns, and {3} stress periods'.format(nlay, nrow, ncol,nper))
            print('   loading laycbd...')
        laycbd = np.empty( (nlay), dtype=np.int)
        d = 0
        while True:
            line = f.readline()
            raw = line.strip('\n').split()
            for val in raw:
                laycbd[d] = np.int(val)
                d += 1
                if d == nlay:
                    break
            if d == nlay:
                break
        #dataset 3 -- delr
        if model.verbose:
            print('   loading delr...')
        delr = util_2d.load(f, model, (1, ncol), np.float32, 'delr',
                            ext_unit_dict)
        delr = delr.array.reshape( (ncol) )
        #dataset 4 -- delc
        if model.verbose:
            print('   loading delc...')
        delc = util_2d.load(f, model, (1, nrow), np.float32, 'delc',
                            ext_unit_dict)
        delc = delc.array.reshape( (nrow) )
        #dataset 5 -- top
        if model.verbose:
            print('   loading top...')
        top = util_2d.load(f, model, (nrow,ncol), np.float32, 'top',
                           ext_unit_dict)
        #dataset 6 -- botm
        if model.verbose:
            print('   loading botm...')
        ncbd=laycbd.sum()
        botm = util_3d.load(f, model, (nlay+ncbd,nrow,ncol), np.float32,
                            'botm', ext_unit_dict)
        #dataset 7 -- stress period info
        if model.verbose:
            print('   loading stress period data...')
        perlen = []
        nstp = []
        tsmult = []
        steady = []
        for k in range(nper):
            line = f.readline()
            a1, a2, a3, a4 = line.strip().split()[0:4]
            a1 = float(a1)
            a2 = int(a2)
            a3 = float(a3)
            if a4.upper() == 'TR':
                a4 = False
            else:
                a4 = True
            perlen.append(a1)
            nstp.append(a2)
            tsmult.append(a3)
            steady.append(a4)

        #--create dis object instance
        dis = ModflowDis(model, nlay, nrow, ncol, nper, delr, delc, laycbd, 
                         top, botm, perlen, nstp, tsmult, steady, itmuni,
                         lenuni)
        #--return dis object instance
        return dis


    def plot(self):
        try:
            import pylab as plt
        except Exception as e:
            print("error importing pylab: " + str(e))
            return

        #get the bas for ibound masking
        bas = self.parent.bas6
        if bas is not None:
            ibnd = bas.getibound()
        else:
            ibnd = np.ones((self.nlay, self.nrow, self.ncol))

        cmap = plt.cm.winter
        cmap.set_bad('w', 1.0)
        fs = 5

        #the width and height of each subplot
        delt = 2.0
        shape = (2, self.nlay+1)
        fig = plt.figure(figsize=(delt+(self.nlay*delt), delt * 2.0))
        #fig = plt.figure()

        #plot the time stepping info in the upper left corner
        ax_time = plt.subplot2grid(shape, (0, 0))
        ax_time.set_title("time stepping information", fontsize=fs)
        idx = np.arange((self.nper))
        width = 0.5
        bars = ax_time.bar(idx, self.perlen, width=width, edgecolor="none",
                    facecolor='b')
        for s, b in zip(self.steady, bars):
            if s:
                b.set_color('b')
            else:
                b.set_color('c')

        ax_time.set_xticks(idx+(width/2.0))
        ax_time.set_xticklabels(idx, fontsize=fs, rotation=90)
        ax_time.set_xlabel("stress period", fontsize=fs)
        ax_time.set_ylabel("time (" + self.itmuni_dict[self.itmuni] + ")",
                           fontsize=fs)
        ax_time.set_yticklabels(ax_time.get_yticks(), fontsize=fs)

        #plot model top in the lower left
        ax_top = plt.subplot2grid(shape, (1, 0),aspect='equal')
        top = self.top.array
        top = np.ma.masked_where(ibnd[0] == 0, top)
        ax_top.set_xlabel("column", fontsize=fs)
        ax_top.set_ylabel("row", fontsize=fs)
        ax_top.imshow(top, cmap=cmap, alpha=0.7, interpolation="none")
        ax_top.set_title("model top - max,min: {0:G},{1:G}"
                         .format(top.max(), top.min()), fontsize=fs)
        ax_top.set_xticklabels(ax_top.get_xticks(), fontsize=fs)
        ax_top.set_yticklabels(ax_top.get_yticks(), fontsize=fs)


        botm = self.botm.array
        for k in range(self.nlay):
            ax_botm = plt.subplot2grid(shape, (0, k+1), aspect="equal")
            ax_thk = plt.subplot2grid(shape, (1, k+1), aspect="equal")
            ax_thk.set_xlabel("column", fontsize=fs)
            ax_thk.set_xlabel("row", fontsize=fs)
            #botm for this layer
            b = botm[k]
            b = np.ma.masked_where(ibnd[k] == 0, b)
            ax_botm.imshow(b,cmap=cmap, alpha=0.7,
                           interpolation="none")
            ax_botm.set_title("botm of layer {0:d} - max,min : {1:G},{2:G}"
                              .format(k+1, b.max(), b.min()), fontsize=fs)
            #thickness of this layer
            if k == 0:
                t = top - botm[k]
            else:
                t = botm[k-1] - botm[k]
            t = np.ma.masked_where(ibnd[k] == 0, t)
            ax_thk.imshow(t,cmap=cmap, alpha=0.7,
                           interpolation="none")
            ax_thk.set_title("thickness of layer {0:d} - max,min : {1:G},{2:G}"
                             .format(k+1, t.max(), t.min()), fontsize=fs)
            ax_thk.set_yticklabels([])
            ax_botm.set_yticklabels([])
            ax_botm.set_xticklabels([])
            ax_thk.set_xlabel("column", fontsize=fs)
            ax_thk.set_xticklabels(ax_thk.get_xticks(), fontsize=fs)
        plt.tight_layout()
        plt.show()


