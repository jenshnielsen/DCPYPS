import time
import sys
import socket
import os
import platform
import numpy as np
from pylab import figure, semilogx, savefig, hist, xlim, ylim, scatter
from pylab import plot, text, title, xlabel, ylabel
#from dcpyps import scplotlib as scpl
from dcpyps import dcio
#from dcpyps import scalcslib as scl

class FitReportHTML():
    """
    """
    def __init__(self, filename=None):


        path, self.filename = set_cwd('fits-dcpyps', filename)
        self.htmlfile = 'report_' + self.filename + '.html'
        self.mecfile = 'mec_' + self.filename + '.yaml'
        self.f = open(self.htmlfile, 'w')
        
        str1 = "DC_PyPs: Q matrix calculations.<br>"
        str2 = ("Date and time of analysis: %4d/%02d/%02d %02d:%02d:%02d<br>"
            %time.localtime()[0:6])
        machine = socket.gethostname()
        system = sys.platform
        str3 = "Machine: %s; System: %s<br>" %(machine, system)
        str = ('<html>\n' + str1 + 'HJCFIT: Fit of model to open-shut times with missed events<br>' +
            '(Uses HJC distributions, exact for first two deadtimes then asymptotic, to calculate likelihood of record)<br>' +
            str2 + str3)
        self.f.write(str)
        
    def rates(self, mec, lik, after_fit=False):
        self.f.write('<br>')
        if after_fit:
            self.f.write('<br>######### FITTED RATE CONSTANTS #########################')
        else:
            self.f.write('<br>######### LOADED RATE CONSTANTS #########################')
        self.f.write('<br>Mechanism: ' + str(mec.mtitle) + '<br>')
        self.f.write('Rates: ' + str(mec.rtitle) + '<br><br>')
        self.f.write('Values of rate constants [1/sec]:<br>')
        self.f.write('<table border="0">')
        for rate in mec.Rates:
            self.f.write('<tr>' + '<td>From ' + str(rate.State1.name) + '</td><td>to ' +
                         str(rate.State2.name) + '</td><td>' + str(rate.name) + 
                         '</td><td>{0:.5g}</td></tr>'.format(rate.unit_rate()))
        self.f.write('</table><br>')
        
        self.f.write('Number of open states = {0:d}<br>'.format(mec.kA))
        self.f.write('Number of short-lived shut states (within burst) = {0:d}<br>'
            .format(mec.kB))
        self.f.write('Number of long-lived shut states (between bursts) = {0:d}<br>'
            .format(mec.kC))
        self.f.write('Number of desensitised states = {0:d}<br><br>'.format(mec.kD))

        self.f.write('Number of cycles = {0:d}<br>'.format(len(mec.Cycles)))
        for i in range(len(mec.Cycles)):
            self.f.write('Cycle {0:d} is formed of states: '.format(i+1))
            for j in range(len(mec.Cycles[i].states)):
                self.f.write(mec.Cycles[i].states[j] + '  ')
            fprod, bprod = mec.check_mr(mec.Cycles[i])
            self.f.write('<br>forward product = {0:.9e}<br>'.format(fprod))
            self.f.write('backward product = {0:.9e}<br>'.format(bprod))
        
        self.f.write ('<br>Likelihood (DCprogs)= {0:.6f}'.format(-lik))
        self.f.write('<br>##################################<br>')
        
    def dataset(self, recs):
        self.f.write('<br>######### DATA SET #########################')
        for i in range(len(recs)):
            self.f.write('<br>Patch # {0:d}'.format(i+1))
            text1 = str(recs[i])
            text = text1.replace('\n', '<br>')
            self.f.write(text)
        self.f.write('##################################<br>')
            
        
    def fit_result(self, mec, start, end, lik, niter):
        self.f.write("<p>DCPROGS fitting finished: %4d/%02d/%02d %02d:%02d:%02d</p>"
        %time.localtime()[0:6])
        self.f.write("<p>Time spent in simplex: {0:.3f} seconds</p>".format(end-start))
        self.f.write('<p>Final log-likelihood = {0:.6f}</p>'.format(-lik))
        self.f.write('<p>Number of iterations = {0:d}</p>'.format(niter))
        
        dcio.mec_save_to_yaml(mec, self.mecfile)
        self.f.write('<p>Fitted rates saved in YAML file: {0}</p>'.
            format(self.mecfile))
        
    def distributions(self, mec, recs):
        
        for i in range(len(recs)):
            name = recs[i].filenames[0][:-4].split('/')[-1]
            op_filename = self.filename + '_open.png'
            sh_filename = self.filename + '_shut.png'
            dcio.png_save_pdf_fig(op_filename, recs[i].opint, mec, 
                recs[i].conc, recs[i].tres, 'open')
            dcio.png_save_pdf_fig(sh_filename, recs[i].shint, mec, 
                recs[i].conc, recs[i].tres, 'shut')
                
            self.f.write("<p>####### Concentration = {0:.3f} microMolar #########</p>".
                format(recs[i].conc*1e6))
            self.f.write("<p>{0} ______________________________ {1}</p>".
                format(op_filename, sh_filename))
            self.f.write("<img src={0} width='450' height='300'>".
                format(os.path.abspath(op_filename)) +
                "<img src={0} width='450' height='300'>".
                format(os.path.abspath(sh_filename)))
                
#            try:
#                mec.set_eff('c', recs[i].conc)
#                text = scl.printout_occupancies(mec, recs[i].tres).replace('\n', '<br>').replace('\t', '&emsp;')
#                self.f.write(text)
#                text = scl.printout_distributions(mec, recs[i].tres).replace('\n', '<br>').replace('\t', '&emsp;')
#                self.f.write(text)
#            except:
#                sys.stderr.write("main: Warning: unable to prepare printout.")

    def finalise(self):
        self.f.write('</html>')
        self.f.close()
        
class ClusterReportHTML():
    """
    """
    def __init__(self, filename, rec, runwin=2, minop=1):
        self.N = runwin # number of openings in sliding frame
        self.minop = minop # minimum number of openings in cluster
        self.clusters = rec.bursts.get_long(minop)
        if self.clusters.count() < 1:
            self.clusters = rec.bursts.get_long(10)
        self.tcrit = rec.tcrit

        self.setup(filename)

    def setup(self, filename):


        path, fname = os.path.split(filename)
        self.fname = fname.split('.')[0]
#        os.chdir(os.path.expanduser("~"))
#        if platform.system() == 'Windows':
#            os.chdir('C://')
#        if not os.path.isdir('clusters'):
#            os.mkdir('clusters')
#        os.chdir('clusters')
#        os.chdir(path)
        if not os.path.isdir(self.fname):
            os.mkdir(self.fname)
        os.chdir(self.fname)
        self.dir = os.getcwd()

        htmlfile = os.path.join(self.fname + '.html')
        self.f = open(htmlfile, 'w')

        str1 = "DC_PyPs: Cluster Inspector.<br>"
        str2 = ("Date and time of analysis: %4d/%02d/%02d %02d:%02d:%02d<br>"
            %time.localtime()[0:6])
        machine = socket.gethostname()
        system = sys.platform
        str3 = "Machine: %s; System: %s<br>" %(machine, system)
        str4 = ('<html>\n' + str1 + str2 + str3)
        self.f.write(str4)

        all_openings, all_shuttings = np.array([]), np.array([])
        popens, shav = np.array([]), np.array([])
        opnum, opav, optot = np.array([]), np.array([]), np.array([])
        for cluster in self.clusters.all():
            all_openings = np.append(all_openings, cluster.get_open_intervals())
            all_shuttings = np.append(all_shuttings, cluster.get_shut_intervals())
            opnum = np.append(opnum, cluster.get_openings_number())
            opav = np.append(opav, cluster.get_openings_average_length())
            optot = np.append(optot, cluster.get_total_open_time())
            shav = np.append(shav, cluster.get_shuttings_average_length())
        popens = self.clusters.get_popen_list()

        self.f.write ('<br>Record in ' + filename + ' contains {0:d} clusters '.
            format(self.clusters.count()) + 'with average Popen = {0:.3f}; '.
            format(np.average(popens)) + 'tcrit = {0:.1f} ms'.
            format(self.tcrit * 1000))
        self.f.write('<br> <br>')
        for cluster in self.clusters.all():
            self.f.write(str(cluster))
            self.f.write('<br>')
        self.f.write('<br> <br>')

        figure(figsize=(6, 4))
        hist(popens, bins=20)
        xlim([0, 1])
        file_popen = os.path.join(self.fname + '_popen.png')
        title(file_popen)
        xlabel('Popen')
        savefig(file_popen, bbox_inches=0)
        self.f.write("<img src={0} width='450' height='300'>".format(file_popen))

        self.insert_pdf(all_openings*1000, 'open', 'Apparent open time, ms')
        self.f.write('<br> <br>')
        self.insert_pdf(all_shuttings*1000, 'shut', 'Apparent shut time, ms')
        self.insert_scatter(opnum, popens, 'OPNUMvPOPENS',
            xtitle='Number of openings per cluster',
            ytitle='Popen')
        self.f.write('<br> <br>')
        self.insert_scatter(opav*1000, popens, 'OPAVvPOPENS',
            xtitle='Average opening length, ms',
            ytitle='Popen')
        self.insert_scatter(optot*1000, popens, 'OPTOTvPOPENS',
            xtitle='Total open time per cluster, ms',
            ytitle='Popen')
        self.f.write('<br> <br>')
        self.insert_scatter(shav*1000, popens, 'SHAVvPOPENS',
            xtitle='Average shutting length, ms',
            ytitle='Popen')
        self.insert_scatter(opav*1000, shav*1000, 'OPAVvSHAV',
            xtitle='Average opening length, ms',
            ytitle='Average shutting length, ms')
        self.f.write('<br> <br>')

        # N - number of openings in sliding frame
        for i in range(self.clusters.count()):
            prm = self.clusters.all()[i].get_running_mean_popen(self.N)
            type = 'Cluster_{0:d}'.format(i+1)
            self.insert_stability_plot(prm, type, self.N, xtitle='Group number',
                ytitle='Mean Popen')

        self.finalise()

    def insert_stability_plot(self, X, type, N, xtitle='', ytitle=''):
        figure(figsize=(6, 4))
        plot(X)
        if ytitle == 'Mean Popen': ylim([0, 1])
        filepath = os.path.join(self.fname + '_' + type + '.png')
        title(filepath)
        text(0.5, 0.9,'Number of intervals in group = {0:d}'.format(2*N))
        xlabel(xtitle)
        ylabel(ytitle)
        savefig(filepath, bbox_inches=0)
        self.f.write("<img src={0} width='450' height='300'>".format(filepath))

    def insert_scatter(self, X, Y, type, xtitle='', ytitle=''):

        figure(figsize=(6, 4))
        scatter(X, Y)
        filepath = os.path.join(self.fname + '_' + type + '.png')
        title(filepath)
        xlabel(xtitle)
        ylabel(ytitle)
        savefig(filepath, bbox_inches=0)
        self.f.write("<img src={0} width='450' height='300'>".format(filepath))

#    def insert_pdf(self, X, type, xtitle=''):
#        figure(figsize=(6, 4))
#        x1, y1, dx = scpl.prepare_hist(X, 0.01)
#        semilogx(x1, y1, 'k-')
#        filepath = os.path.join(self.fname + '_' + type + '.png')
#        title(filepath)
#        xlabel(xtitle)
#        savefig(filepath, bbox_inches=0)
#        self.f.write("<img src={0} width='450' height='300'>".format(filepath))

    def finalise(self):
        self.f.write('</html>')
        self.f.close()


def set_cwd(dirname, filename):
    os.chdir(os.path.expanduser("~"))
    if platform.system() == 'Windows':
        os.chdir('C://')
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    os.chdir(dirname)

    if not filename:
        filename = ("%4d%02d%02d_%02d%02d%02d" %time.localtime()[0:6])
    os.mkdir(filename)
    os.chdir(filename)

    return os.getcwd(), filename


