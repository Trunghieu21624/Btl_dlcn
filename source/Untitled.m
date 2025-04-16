T = readtable('mau_tai_4.7.csv');       
value = T.RealValue;

% Tính trung bình b? qua NaN
avg_temp = mean(value(~isnan(value)));

% V? d? li?u
plot(value, '.', 'MarkerSize', 10);  
hold on;

% V? ???ng trung bình
plot([1, length(value)], [avg_temp, avg_temp], '--r', 'LineWidth', 2);  

% Hi?n th? giá tr? trung bình trên ?? th?
% Tính v? trí góc trên bên ph?i d?a trên gi?i h?n tr?c
x_pos = xlim;  % [xmin xmax]
y_pos = ylim;  % [ymin ymax]

% Hi?n th? giá tr? trung bình ? góc trên bên ph?i
text(x_pos(2)*0.95, y_pos(2)*0.95, sprintf('Trung bình: %.2f', avg_temp), ...
    'HorizontalAlignment', 'right', 'Color', 'r', 'FontWeight', 'bold', 'FontSize', 10);

xlabel('');
ylabel('RealValue');
title('Tu dien 47 muy');
ylim([0, 20]);
grid on;
hold off;
