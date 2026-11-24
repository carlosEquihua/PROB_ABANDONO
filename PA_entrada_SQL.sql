--==================================================================================
----------------------------------HISTORICO-----------------------------------------
--==================================================================================
SELECT dc.ClaveCliente,df.Ano,df.Mes,COUNT(DISTINCT vv.Num_nota) AS Notas_Acumuladas,
    -- VARIABLE DE FRICCI�N: DEVOLUCIONES
    COUNT(DISTINCT CASE WHEN vv.vta_Neta < 0 THEN vv.Num_nota END) AS Notas_Devolucion,
    (COUNT(DISTINCT CASE WHEN vv.vta_Neta < 0 THEN vv.Num_nota END) * 1.0) 
    / NULLIF(COUNT(DISTINCT vv.Num_nota), 0) AS Tasa_Devoluciones,
    -- VARIABLE DE ANCLAJE: PENETRACI�N DE MARCA PROPIA (Variedad)
    COUNT(DISTINCT da.articulo) AS Variedad_Articulos_Totales,
    -- lista de marca propia
    COUNT(DISTINCT CASE WHEN da.articulo IN (
        '1400611', '1400609', '1400608', '4661061', '9984284', '9984283', '9984386', '9984385', '4753009', '9995589', 
        '4751004', '9995587', '4751006', '9201629', '4513020', '1400603', '5100101', '4701683', '4701682', '4701684', 
        '9205042', '7701042', '9900652', '9200511', '9900656', '9900655', '9900658', '9900654', '7201014', '7201013', 
        '5500317', '5500318', '9606573', '5943111', '7100485', '9201631', '2670302', '2670304', '9205051', '2665017', 
        '2665019', '2665018', '1901013', '1400507', '9900406', '9900407', '9900414', '9900433', '9900428', '9900426', 
        '9900431', '9201625', '9900416', '9900429', '9900432', '8608110', '9984034', '1323021', '8509009', '2291008', 
        '2222218', '2291026', '2291032', '2351441', '2351440', '2351437', '5870060', '0319211', '00410268', '9000723', 
        '6701024', '6701023', '9983446', '9983447', '9900504', '9900505', '4502608', '9201506', '4513022', '4513023', 
        '3436512', '5941526', '3436516', '1000016', '1001028', '4512904', '9000205', '0000005', '4760311', '4760312', 
        '4760310', '8608026', '8608029', '8608028', '8608031', '9995103', '9995104', '00319211', '01805031', '01805125', 
        '14006000', '9260207', '9260208', '9260214', '9260216', '2292022', '2292010', '2351107', '2665021', '2665023', 
        '2665022', '2304005', '2304008', '9205041', '2670024', '2600003', '4661032', '4661028', '4661029', '4661063', 
        '4661064', '4760315', '1323020', '2670027', '4753019', '8608027', '0319213', '9995585'
    ) THEN da.articulo END) AS Variedad_Marca_Propia,
    -- 3. Tasa de Penetraci�n: porcentaje de carrito en Marca Propia
    (COUNT(DISTINCT CASE WHEN da.articulo IN (
        '1400611', '1400609', '1400608', '4661061', '9984284', '9984283', '9984386', '9984385', '4753009', '9995589', 
        '4751004', '9995587', '4751006', '9201629', '4513020', '1400603', '5100101', '4701683', '4701682', '4701684', 
        '9205042', '7701042', '9900652', '9200511', '9900656', '9900655', '9900658', '9900654', '7201014', '7201013', 
        '5500317', '5500318', '9606573', '5943111', '7100485', '9201631', '2670302', '2670304', '9205051', '2665017', 
        '2665019', '2665018', '1901013', '1400507', '9900406', '9900407', '9900414', '9900433', '9900428', '9900426', 
        '9900431', '9201625', '9900416', '9900429', '9900432', '8608110', '9984034', '1323021', '8509009', '2291008', 
        '2222218', '2291026', '2291032', '2351441', '2351440', '2351437', '5870060', '0319211', '00410268', '9000723', 
        '6701024', '6701023', '9983446', '9983447', '9900504', '9900505', '4502608', '9201506', '4513022', '4513023', 
        '3436512', '5941526', '3436516', '1000016', '1001028', '4512904', '9000205', '0000005', '4760311', '4760312', 
        '4760310', '8608026', '8608029', '8608028', '8608031', '9995103', '9995104', '00319211', '01805031', '01805125', 
        '14006000', '9260207', '9260208', '9260214', '9260216', '2292022', '2292010', '2351107', '2665021', '2665023', 
        '2665022', '2304005', '2304008', '9205041', '2670024', '2600003', '4661032', '4661028', '4661029', '4661063', 
        '4661064', '4760315', '1323020', '2670027', '4753019', '8608027', '0319213', '9995585'
    ) THEN da.articulo END) * 1.0)
    / NULLIF(COUNT(DISTINCT da.articulo), 0) AS Penetracion_Marca_Propia,
    COUNT(DISTINCT TRIM(ds.NombreSublinea)) AS Variedad_Categoria,SUM(vv.vta_Neta) AS Venta_Acumulada,
    SUM(vv.Cos_Ven) AS Costo_Acumulado,
    -- VARIABLES TEMPORALES:
    MAX(df.Fecha) AS Ultima_Compra_Mes,          
    COUNT(DISTINCT df.Fecha) AS Dias_Compra_Mes  
INTO TEMP_CAEL_HIST_3_OCTUBRE
--TEMP_CAEL_HIST_3_JULIO
--TEMP_CAEL_HIST_3_Enero
--TEMP_CAEL_HIST_3_JUNIO
FROM ventas.Ventas AS vv 
INNER JOIN dim.Fechas AS df ON vv.ID_Date = df.ID_date
INNER JOIN dim.Articulos AS da ON vv.ID_Art = da.ID_Art
INNER JOIN dim.clientes AS dc ON vv.ID_Cte = dc.Id_Cte
INNER JOIN dim.Slineas AS ds ON da.SubLinea = ds.Sublinea
INNER JOIN dim.Sucursales AS dsu ON vv.ID_Suc = dsu.ID_Suc
WHERE df.Fecha BETWEEN '20250901' AND '20260930'
  AND dc.ClaveCliente NOT IN ('000000001') 
  AND dc.ClaveCliente NOT LIKE '%[a-zA-Z]%' 
  AND vv.Id_Suc NOT IN (SELECT id_suc FROM dim.sucursales_omitir)
GROUP BY dc.ClaveCliente,df.Ano,df.Mes
------------------------------------------------------------------------------------
--PRIMER TABLA CENTRAL HISTORICO
SELECT * FROM TEMP_CLAS_PROB_ABAN_CAEL_V3_AGOSTO
--DROP TABLE TEMP_CAEL_HIST_3_AGOSTO
--DROP TABLE BI_agosto_class
SELECT * FROM TEMP_CAEL_HIST_3_AGOSTO
SELECT * FROM BI_agosto_class
--==================================================================================
---------------------------------------FOTO-----------------------------------------
--==================================================================================
------------------------------------------------------------------------------------
declare @f_inicio varchar (8)
declare @f_fin    varchar (8)
select @f_inicio  = '20250701'
select @f_fin     = '20260731'
--INSUMO 1: Ranking_File_2026XX
SELECT  Clave, avg(Frecuencia) Dias_prom, avg(VentaNeta) Com_Mens_Prom
into #Temp1
from (
SELECT c.clavecliente Clave, f.ano||f.mes Periodo, sum(v.Vta_Neta) VentaNeta, count(distinct f.fecha) Frecuencia
from ventas.ventas v
  inner join dim.clientes c on v.id_cte = c.id_cte
  inner join dim.fechas f on v.id_date = f.id_date
  --inner join dim.sucursales s on v.id_suc = s.id_suc
where f.fecha between @f_inicio and @f_fin
and v.Id_Suc NOT IN (select id_suc from dim.sucursales_omitir)
  and v.ID_Cte <> 1
and  c.clavecliente not in ('000000001','000001000','00000GABY','00LETICIA','00LILIANA','ALMA ROSA','00ADRIANA',
'000CARMEN','0000MARIO','0000MARCO','00000BETY','CED000007','000000E04','000000E03','000000E01','000000F01','000000G01')
group by c.clavecliente, f.ano||f.mes
) A
group by Clave

select a.id_cte, a.clavecliente clave, a.variedad categorias, a.skus,a.totalmeses meses_compra, a.totaldiascompra dias_compra, 
a.vta venta_neta, a.costo, a.transacciones,  t.Com_Mens_Prom, t.Dias_prom,mesulti, 
--clasif_nueva, 
b.suc,a.vta_3_meses venta_trimestral 
into temp_insum1
from (
select v.ID_Cte, c.clavecliente ,count(distinct ar.sublinea) variedad,count(distinct ar.id_art) skus,
count(distinct  f.ano||f.mes) totalmeses,count (distinct v.id_date) totaldiascompra,sum(v.vta_neta) vta,
sum(v.cos_ven) costo,count(distinct v.num_nota) transacciones, count(distinct s.id_suc) sucursales, max(convert(int,f.ano||f.mes)) mesulti,
--rtrim(cf.clasificacion_mensual) clasif_nueva,
sum(case when fecha between '20260501' and  '20260731' then v.Vta_Neta end) vta_3_meses --LM01
from ventas.ventas v 
inner join dim.fechas f on v.id_date = f.id_date 
inner join dim.clientes c on v.id_cte = c.id_cte 
inner join dim.articulos ar on v.id_art = ar.id_art
inner join dim.sucursales s on v.id_suc = s.id_suc
--inner join clientes_clasificacion_emp_cf2 cf on v.id_cte = cf.id_cte
where f.fecha between @f_inicio and  @f_fin 
and   v.id_suc not in (select id_suc from dim.sucursales_omitir)
and  c.clavecliente not in ('000000001')
group by c.clavecliente,v.ID_Cte -- clasif_nueva, v.ID_Cte
 ) a
 inner join (
select * from (
select a.id_cte , a.suc , vta , row_number ( ) over (partition by  a.id_cte  order by vta desc ) val 
from (
select v.id_cte , s.suc , sum(v.vta_neta) vta
from ventas.ventas v inner join dim.fechas f on v.id_date = f.id_date 
inner join dim.clientes c on v.id_cte = c.id_cte   
inner join dim.sucursales s on v.id_suc = s.id_suc
where f.fecha between @f_Inicio  and  @f_Fin 
and   v.id_suc not in (select id_suc from dim.sucursales_omitir)
and  c.clavecliente not in ('000000001','000001000','00000GABY','00LETICIA','00LILIANA','ALMA ROSA','00ADRIANA',
'000CARMEN','0000MARIO','0000MARCO','00000BETY','CED000007','000000E04','000000E03','000000E01','000000F01','000000G01')
group by  v.id_cte , s.suc 
) a ) a 
where val = 1 ) b 
on a.id_cte = b.id_cte
inner join #temp1 t
on t.clave=a.clavecliente
group by a.id_cte, a.clavecliente, a.variedad , a.skus ,a.totalmeses , a.totaldiascompra, a.vta , a.costo, a.transacciones,mesulti,-- clasif_nueva,
 b.suc, a.vta_3_meses, t.Com_Mens_Prom, t.Dias_prom
----------------------------------------------------------------------------------
----Query que extrae la �ltima compra y la recency

declare @f_inicio varchar (8)
declare @f_fin    varchar (8)
select @f_inicio  = '20250701'
select @f_fin     = '20260731'
--INSUMO DE PASO - recency
select  cli.ClaveCliente,max(dates.Fecha) Ultima_compra,
  DATEDIFF(day, CAST(max(dates.Fecha) AS TIMESTAMP), '2026/07/31') DiasUltimaCompra
into recency
from ventas.ventas sales,
dim.Fechas dates,
dim.clientes cli
where sales.ID_Date = dates.ID_date
and sales.ID_Cte = cli.Id_Cte
and dates.Fecha between '20250701' and '20260731'
group by cli.ClaveCliente
-----------------------------------------------------------------------------------
declare @f_inicio varchar (8)
declare @f_fin    varchar (8)
select @f_inicio  = '20250701'
select @f_fin     = '20260731'
--INSUMO DE PASO - tiempo_zorro
select cli.ClaveCliente,clix.fec_alta fec_alta,DATEDIFF(day, CAST(clix.fec_alta AS TIMESTAMP),'2026/07/31') Tiempo_Zorro
into tiempo_zorro
from dim.clientes cli,
clientes.cxccli clix 
where clix.cve = cli.ClaveCliente
and cli.ClaveCliente in (
select 
cli.ClaveCliente
from ventas.ventas sales,
dim.Fechas dates,
dim.clientes cli
where sales.ID_Date = dates.ID_date
and sales.ID_Cte = cli.Id_Cte
and dates.Fecha between '20250701' and '20260731'
group by cli.ClaveCliente
)
--Insumo 2: Variables_Tiempo_2026XX
select r.*,t.fec_alta,t.Tiempo_Zorro
into temp_insum2
from recency as r inner join tiempo_zorro as t
on r.ClaveCliente = t.ClaveCliente
--------------------------------------------------------------
declare @f_inicio varchar (8)
declare @f_fin    varchar (8)
select @f_inicio  = '20250701'
select @f_fin     = '20260731'

select cli.ClaveCliente ClaveCliente,sum(Vta_Neta) Venta_Acumulada_Mes 
--Insumo 3: Gasto_Final_2026XX
into temp_insum3
from ventas.ventas sales,
dim.Fechas dates,
dim.clientes cli
where sales.ID_Date = dates.ID_date
and sales.ID_Cte = cli.Id_Cte
and dates.Fecha between substring(@f_fin,1,6)||'01' and @f_fin
group by cli.ClaveCliente
--------------------------------------------------------------
--Insumo de consumo final: Consumible final
select Iu.*,Id.Ultima_compra,Id.DiasUltimaCompra,Id.fec_alta,
Id.Tiempo_Zorro,It.Venta_Acumulada_Mes
into BI_Octubre_class
from temp_insum1 as Iu 
left join temp_insum2 as Id on Iu.clave=Id.ClaveCliente 
left join temp_insum3 as It on Iu.Clave=It.ClaveCliente
------------------------------------------------------------------------------------
--SEGUNDA TABLA CENTRAL FOTO
SELECT * FROM BI_Octubre_class
--==================================================================================
--Borrado de tablas
DROP TABLE temp_insum1
DROP TABLE recency
DROP TABLE tiempo_zorro
DROP TABLE temp_insum2
DROP TABLE temp_insum3

