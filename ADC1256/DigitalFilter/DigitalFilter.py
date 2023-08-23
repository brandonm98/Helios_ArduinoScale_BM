import numpy as np
import scipy.signal as signal

class LPF(object):
    def createCoeffs(self,order,cutoff,filterType,design='butter',rp=1,rs=1,fs=0):
        self.COEFFS = [0]
        for i in range(len(cutoff)):
            cutoff[i] = cutoff[i]/fs*2
        self.COEFFS = signal.butter(order,cutoff,filterType,output='sos')
        return self.COEFFS
        
    def __init__(self,order,cutoff,filterType,design='butter',rp=1,rs=1,fs=0):
        self.COEFFS = self.createCoeffs(order,cutoff,filterType,design,rp,rs,fs)
        self.acc_input = np.zeros(len(self.COEFFS))
        self.acc_output = np.zeros(len(self.COEFFS))
        self.buffer1 = np.zeros(len(self.COEFFS))
        self.buffer2 = np.zeros(len(self.COEFFS))
        self.input = 0
        self.output = 0

    def filter(self,input):
        if len(self.COEFFS[0,:]) > 1:
        
            self.input = input
            self.output = 0

            for i in range(len(self.COEFFS)):
                
                self.FIRCOEFFS = self.COEFFS[i][0:3]
                self.IIRCOEFFS = self.COEFFS[i][3:6]

                self.acc_input[i] = (self.input + self.buffer1[i] 
                * -self.IIRCOEFFS[1] + self.buffer2[i] * -self.IIRCOEFFS[2])
                    
                self.acc_output[i] = (self.acc_input[i] * self.FIRCOEFFS[0]
                + self.buffer1[i] * self.FIRCOEFFS[1] + self.buffer2[i] 
                * self.FIRCOEFFS[2])
                
                self.buffer2[i] = self.buffer1[i]
                self.buffer1[i] = self.acc_input[i]
                
                self.input = self.acc_output[i]
            
            self.output = self.acc_output[i]
                
        return self.output
