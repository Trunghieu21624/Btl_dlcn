T = readtable('mau_tai_4.7.csv');       
value = T.RealValue;

% T�nh trung b�nh b? qua NaN
avg_temp = mean(value(~isnan(value)));

% V? d? li?u
plot(value, '.', 'MarkerSize', 10);  
hold on;

% V? ???ng trung b�nh
plot([1, length(value)], [avg_temp, avg_temp], '--r', 'LineWidth', 2);  

% Hi?n th? gi� tr? trung b�nh tr�n ?? th?
% T�nh v? tr� g�c tr�n b�n ph?i d?a tr�n gi?i h?n tr?c
x_pos = xlim;  % [xmin xmax]
y_pos = ylim;  % [ymin ymax]

% Hi?n th? gi� tr? trung b�nh ? g�c tr�n b�n ph?i
text(x_pos(2)*0.95, y_pos(2)*0.95, sprintf('Trung b�nh: %.2f', avg_temp), ...
    'HorizontalAlignment', 'right', 'Color', 'r', 'FontWeight', 'bold', 'FontSize', 10);

xlabel('');
ylabel('RealValue');
title('Tu dien 47 muy');
ylim([0, 20]);
grid on;
hold off;
