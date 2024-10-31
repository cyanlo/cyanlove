# 开发说明
## 整体界面如下图：

![Image](https://github.com/cyanlo/cyanloveQGIS/blob/main/images/img1.jpg)

## 功能1：提取栅格数据可进行分析，并显示邻区信息.
输入CGI格式(基站ID-CELLID)：如：45666-123.
点击查询按钮，则显示如下图所示的栅格，其中红色为弱覆盖栅格，绿色为较好的栅格。
![Image](https://github.com/cyanlo/cyanloveQGIS/blob/main/images/img2.png)
## 功能2：导出图层边界WKT集
选择需要导出边界的图层，输出最终的WKT格式边界信息。
## 功能3：导入文件绘制图形
可以选择CSV或者excel文件，设置边界格式，最终绘制成图形。
![Image](https://github.com/cyanlo/cyanloveQGIS/blob/main/images/img3.png)
## 功能4：导入CSV或者excel文件到数据库
![Image](https://github.com/cyanlo/cyanloveQGIS/blob/main/images/img4.png)
## 功能5：导入CSV或者excel文件，选择经纬度列，创建点图层
![Image](https://github.com/cyanlo/cyanloveQGIS/blob/main/images/img5.png)
## 功能6：输入点，线，面格式，绘制图形
 点：输入wkt格式，或者 
 106.123,26.344
 107.442,26.555
 107.123,26.344
 108.442,25.555
 线：输入wkt格式，或者 106.123,26.344; 107.442,26.555; 107.123,26.344
 面：输入wkt格式，或者 106.123,26.344; 107.442,26.555; 107.123,26.344

![Image](https://github.com/cyanlo/cyanloveQGIS/blob/main/images/img6.png)