function blkStruct = slblocks
% This function specifies that the library 'simulink_gym.slx'
% should appear in the Library Browser with the 
% name 'Simulink Gym'

    Browser.Library = 'simulink_gym';
    % 'simulink_gym' is the name of the library

    Browser.Name = 'Simulink Gym';
    % 'Simulink Gym' is the library name that appears
    % in the Library Browser

    blkStruct.Browser = Browser;