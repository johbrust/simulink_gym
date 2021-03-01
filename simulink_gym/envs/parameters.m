% Script defining parameters for cartpole simulation.

% General parameters:
params.general.tsim_s   = 10;               % [s]       Simulation time
params.general.g        = 9.80665;         % [m/s²]    Gravitational constant
params.general.dT       = 0.001;            % [s]       Discrete step time

% Cart parameters:
params.cart.mass_kg     = 1;                % [kg]      Mass of cart
params.cart.x0          = 0;                % [m]       Starting position of cart

% Pole parameters:
params.pole.mass_kg     = 0.1;              % [kg]      Mass of pole
params.pole.length_m    = 0.5;              % [m]       Distance between CoM and center of rotation
params.pole.theta0_deg  = 24*rand(1)-12;    % [°]       Starting angle of pole