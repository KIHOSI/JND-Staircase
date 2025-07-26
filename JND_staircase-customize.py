"""measure your JND in orientation using a staircase method with proper reversal detection"""
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy, random
import csv

class CustomStaircase:
    def __init__(self, startVal=45, stepSizes=[10, 5, 2], minVal=0, maxVal=90, 
                 nUp=1, nDown=3, maxReversals=6, maxTrials=50):
        self.startVal = startVal
        self.stepSizes = stepSizes
        self.minVal = minVal
        self.maxVal = maxVal
        self.nUp = nUp  # number of incorrect responses to go easier (increase step)
        self.nDown = nDown  # number of correct responses to go harder (decrease step)
        self.maxReversals = maxReversals
        self.maxTrials = maxTrials
        
        # Current state
        self.currentVal = startVal
        self.currentStepSize = stepSizes[0]
        self.stepSizeIndex = 0
        self.trialNum = 0
        self.finished = False
        
        # Response tracking
        self.responses = []  # list of 1 (correct) or -1 (incorrect)
        self.values = []     # stimulus values for each trial
        self.consecutiveCorrect = 0
        self.consecutiveIncorrect = 0
        
        # Reversal tracking
        self.reversals = []
        self.reversalIntensities = []
        self.lastDirection = None  # 'harder' or 'easier'
        
    def addResponse(self, correct):
        """Add a response and update the staircase"""
        if self.finished:
            return
            
        # Record the response
        response = 1 if correct else -1
        self.responses.append(response)
        self.values.append(self.currentVal)
        self.trialNum += 1
        
        # Update consecutive counters
        if correct:
            self.consecutiveCorrect += 1
            self.consecutiveIncorrect = 0
        else:
            self.consecutiveIncorrect += 1
            self.consecutiveCorrect = 0
        
        # Determine if we need to change difficulty
        changeDirection = None
        
        if self.consecutiveCorrect >= self.nDown:
            # Make it harder (decrease stimulus difference)
            changeDirection = 'harder'
            self.consecutiveCorrect = 0
            
        elif self.consecutiveIncorrect >= self.nUp:
            # Make it easier (increase stimulus difference)  
            changeDirection = 'easier'
            self.consecutiveIncorrect = 0
        
        # Check for reversal
        if changeDirection is not None:
            if self.lastDirection is not None and self.lastDirection != changeDirection:
                # This is a reversal!
                self.reversals.append(self.trialNum)
                self.reversalIntensities.append(self.currentVal)
                print(f"REVERSAL #{len(self.reversals)} at trial {self.trialNum}: {self.currentVal}")
                
                # Update step size after certain number of reversals
                if len(self.reversals) == 2 and self.stepSizeIndex < len(self.stepSizes) - 1:
                    self.stepSizeIndex += 1
                    self.currentStepSize = self.stepSizes[self.stepSizeIndex]
                    print(f"Step size changed to: {self.currentStepSize}")
                elif len(self.reversals) == 4 and self.stepSizeIndex < len(self.stepSizes) - 1:
                    self.stepSizeIndex += 1
                    self.currentStepSize = self.stepSizes[self.stepSizeIndex]
                    print(f"Step size changed to: {self.currentStepSize}")
            
            # Update the stimulus value
            if changeDirection == 'harder':
                self.currentVal = max(self.minVal, self.currentVal - self.currentStepSize)
            else:  # easier
                self.currentVal = min(self.maxVal, self.currentVal + self.currentStepSize)
            
            self.lastDirection = changeDirection
            print(f"Direction: {changeDirection}, New value: {self.currentVal}")
        
        # Check if finished
        if len(self.reversalIntensities) >= self.maxReversals or self.trialNum >= self.maxTrials:
            self.finished = True
            print(f"Staircase finished after {self.trialNum} trials")
    
    def getNextVal(self):
        """Get the next stimulus value"""
        return self.currentVal


# Log file
dataFile = open('blade_JND_data_fixed.csv', 'w', newline='')
writer = csv.writer(dataFile)
writer.writerow(['trial', 'targetSide', 'bladeAngle', 'response', 'correct', 'reversal'])

# create the custom staircase handler
staircase = CustomStaircase(startVal=45,
                           stepSizes=[10, 5, 2], 
                           minVal=0,
                           maxVal=90,
                           nUp=1, 
                           nDown=3,  # will home in on the 80% threshold
                           maxReversals=6,
                           maxTrials=50)

# create window
win = visual.Window([800,600], allowGUI=True,
                    monitor='testMonitor', units='deg')

# Create stimuli
fixation = visual.TextStim(win, text='+', height=1)
blade_left = visual.Rect(win, width=1, height=5, fillColor='white', pos=(-5, 0))
blade_right = visual.Rect(win, width=1, height=5, fillColor='white', pos=(5, 0))

# display instructions and wait
message1 = visual.TextStim(win, pos=[0,+3], text='Hit a key when ready.')
message2 = visual.TextStim(win, pos=[0,-3],
    text="Press 'left' if the first stimulus felt stronger, 'right' if the second did.")
message3 = visual.TextStim(win, pos=[0,-5],
    text="Press 'space' to repeat the trial if unsure.")
message1.draw()
message2.draw()
message3.draw()
fixation.draw()
win.flip()
event.waitKeys()

# Experiment loop
while not staircase.finished:
    bladeAngle = staircase.getNextVal()
    print(f"Trial #{staircase.trialNum + 1}, bladeAngle = {bladeAngle}")
    
    # randomly pick which side shows the angle (left or right)
    targetSide = random.choice(['left', 'right'])

    if targetSide == 'left':
        angle_left = 90
        angle_right = 90 - bladeAngle
    else:
        angle_left = 90 - bladeAngle
        angle_right = 90

    # apply rotation to blades
    blade_left.ori = 90 - angle_left
    blade_right.ori = 90 - angle_right

    # allow repeat trial until users click 'left' or 'right'
    repeatTrial = True
    while repeatTrial:
        # show fixation
        fixation.draw()
        win.flip()
        core.wait(0.5)

        # show stimuli
        blade_left.draw()
        blade_right.draw()
        win.flip()

        # get response
        thisResp = None
        repeatNow = False
        while thisResp is None:
            allKeys = event.waitKeys(keyList=['left', 'right', 'space', 'q', 'escape'])
            print("Key pressed:", allKeys)
            for thisKey in allKeys:
                if thisKey == 'space':
                    print("Repeating trial...")
                    repeatNow = True
                    break
                elif thisKey == 'left':
                    if targetSide == 'left': 
                        thisResp = 1  # correct
                    else: 
                        thisResp = -1  # incorrect
                    repeatTrial = False
                elif thisKey == 'right':
                    if targetSide == 'right': 
                        thisResp = 1  # correct
                    else: 
                        thisResp = -1  # incorrect
                    repeatTrial = False
                elif thisKey in ['q', 'escape']:
                    core.quit()  # abort experiment
            event.clearEvents()

            if repeatNow:
                break

    # update staircase
    correct = (thisResp == 1)
    print(f"Response: {thisKey}, Correct: {correct}")
    
    # Check if this trial resulted in a reversal
    prev_reversals = len(staircase.reversalIntensities)
    staircase.addResponse(correct)
    is_reversal = len(staircase.reversalIntensities) > prev_reversals

    # log data
    writer.writerow([staircase.trialNum, targetSide, bladeAngle, thisKey, thisResp, is_reversal])

    # inter-trial interval
    fixation.draw()
    win.flip()
    core.wait(1)

# staircase has ended
dataFile.close()

# give some output to user
print('reversals:')
print(staircase.reversalIntensities)
if len(staircase.reversalIntensities) >= 6:
    approxThreshold = numpy.average(staircase.reversalIntensities[-6:])
    print('mean of final 6 reversals = %.3f' % (approxThreshold))

    # give some on-screen feedback
    feedback1 = visual.TextStim(
            win, pos=[0,+3],
            text='mean of final 6 reversals = %.3f' % (approxThreshold))
else:
    feedback1 = visual.TextStim(
            win, pos=[0,+3],
            text=f'Experiment ended with {len(staircase.reversalIntensities)} reversals')

feedback1.draw()
fixation.draw()
win.flip()
event.waitKeys()

win.close()
core.quit()