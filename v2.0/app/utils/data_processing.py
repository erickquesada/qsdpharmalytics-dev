import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json
import re
from decimal import Decimal, ROUND_HALF_UP

@dataclass
class DataCleaningResult:
    """Resultado da limpeza de dados"""
    original_count: int
    cleaned_count: int
    removed_count: int
    cleaning_log: List[str]
    data: pd.DataFrame

class DataProcessor:
    """Classe principal para processamento de dados"""
    
    @staticmethod
    def clean_sales_data(df: pd.DataFrame) -> DataCleaningResult:
        """Limpar e validar dados de vendas"""
        
        original_count = len(df)
        cleaning_log = []
        
        # Cópia para não modificar original
        cleaned_df = df.copy()
        
        # 1. Remover registros com valores nulos críticos
        critical_columns = ['product_name', 'quantity', 'unit_price']
        initial_nulls = cleaned_df[critical_columns].isnull().any(axis=1).sum()
        
        if initial_nulls > 0:
            cleaned_df = cleaned_df.dropna(subset=critical_columns)
            cleaning_log.append(f"Removidos {initial_nulls} registros com campos críticos nulos")
        
        # 2. Validar e corrigir tipos de dados
        if 'quantity' in cleaned_df.columns:
            # Converter para inteiro, remover valores inválidos
            cleaned_df['quantity'] = pd.to_numeric(cleaned_df['quantity'], errors='coerce')
            invalid_qty = cleaned_df['quantity'].isnull().sum()
            if invalid_qty > 0:
                cleaned_df = cleaned_df.dropna(subset=['quantity'])
                cleaning_log.append(f"Removidos {invalid_qty} registros com quantidade inválida")
            
            # Remover quantidades negativas ou zero
            negative_qty = (cleaned_df['quantity'] <= 0).sum()
            if negative_qty > 0:
                cleaned_df = cleaned_df[cleaned_df['quantity'] > 0]
                cleaning_log.append(f"Removidos {negative_qty} registros com quantidade <= 0")
        
        # 3. Validar preços
        if 'unit_price' in cleaned_df.columns:
            cleaned_df['unit_price'] = pd.to_numeric(cleaned_df['unit_price'], errors='coerce')
            invalid_price = cleaned_df['unit_price'].isnull().sum()
            if invalid_price > 0:
                cleaned_df = cleaned_df.dropna(subset=['unit_price'])
                cleaning_log.append(f"Removidos {invalid_price} registros com preço inválido")
            
            # Remover preços negativos ou zero
            negative_price = (cleaned_df['unit_price'] <= 0).sum()
            if negative_price > 0:
                cleaned_df = cleaned_df[cleaned_df['unit_price'] > 0]
                cleaning_log.append(f"Removidos {negative_price} registros com preço <= 0")
        
        # 4. Limpar nomes de produtos
        if 'product_name' in cleaned_df.columns:
            cleaned_df['product_name'] = cleaned_df['product_name'].str.strip()
            cleaned_df['product_name'] = cleaned_df['product_name'].str.title()
            
            # Remover produtos com nomes muito curtos
            short_names = (cleaned_df['product_name'].str.len() < 3).sum()
            if short_names > 0:
                cleaned_df = cleaned_df[cleaned_df['product_name'].str.len() >= 3]
                cleaning_log.append(f"Removidos {short_names} registros com nome de produto muito curto")
        
        # 5. Padronizar categorias
        if 'product_category' in cleaned_df.columns:
            cleaned_df['product_category'] = cleaned_df['product_category'].str.strip()
            cleaned_df['product_category'] = cleaned_df['product_category'].str.title()
            
            # Mapear variações comuns
            category_mapping = {
                'Analgesico': 'Analgésicos',
                'Analgesicos': 'Analgésicos',
                'Anti-Inflamatorio': 'Anti-inflamatórios',
                'Antiinflamatorio': 'Anti-inflamatórios',
                'Antibiotico': 'Antibióticos',
                'Antibioticos': 'Antibióticos'
            }
            
            cleaned_df['product_category'] = cleaned_df['product_category'].replace(category_mapping)
        
        # 6. Validar datas
        if 'sale_date' in cleaned_df.columns:
            cleaned_df['sale_date'] = pd.to_datetime(cleaned_df['sale_date'], errors='coerce')
            invalid_dates = cleaned_df['sale_date'].isnull().sum()
            if invalid_dates > 0:
                cleaned_df = cleaned_df.dropna(subset=['sale_date'])
                cleaning_log.append(f"Removidos {invalid_dates} registros com data inválida")
            
            # Remover datas futuras
            future_dates = (cleaned_df['sale_date'] > datetime.now()).sum()
            if future_dates > 0:
                cleaned_df = cleaned_df[cleaned_df['sale_date'] <= datetime.now()]
                cleaning_log.append(f"Removidos {future_dates} registros com data futura")
        
        # 7. Calcular total_price se não existir
        if 'total_price' not in cleaned_df.columns:
            if 'quantity' in cleaned_df.columns and 'unit_price' in cleaned_df.columns:
                cleaned_df['total_price'] = cleaned_df['quantity'] * cleaned_df['unit_price']
                if 'discount' in cleaned_df.columns:
                    cleaned_df['total_price'] -= cleaned_df['discount'].fillna(0)
                cleaning_log.append("Calculado total_price automaticamente")
        
        # 8. Limpar nomes de farmácias
        if 'pharmacy_name' in cleaned_df.columns:
            cleaned_df['pharmacy_name'] = cleaned_df['pharmacy_name'].str.strip()
            cleaned_df['pharmacy_name'] = cleaned_df['pharmacy_name'].str.title()
        
        cleaned_count = len(cleaned_df)
        removed_count = original_count - cleaned_count
        
        return DataCleaningResult(
            original_count=original_count,
            cleaned_count=cleaned_count,
            removed_count=removed_count,
            cleaning_log=cleaning_log,
            data=cleaned_df
        )
    
    @staticmethod
    def detect_outliers(
        df: pd.DataFrame, 
        column: str, 
        method: str = "iqr"
    ) -> Tuple[pd.DataFrame, List[int]]:
        """Detectar outliers em uma coluna"""
        
        if column not in df.columns:
            raise ValueError(f"Coluna '{column}' não encontrada no DataFrame")
        
        data = df[column].copy()
        outlier_indices = []
        
        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_indices = data[(data < lower_bound) | (data > upper_bound)].index.tolist()
        
        elif method == "zscore":
            z_scores = np.abs((data - data.mean()) / data.std())
            outlier_indices = data[z_scores > 3].index.tolist()
        
        elif method == "modified_zscore":
            median = data.median()
            mad = np.median(np.abs(data - median))
            modified_z_scores = 0.6745 * (data - median) / mad
            outlier_indices = data[np.abs(modified_z_scores) > 3.5].index.tolist()
        
        clean_df = df.drop(outlier_indices)
        
        return clean_df, outlier_indices
    
    @staticmethod
    def aggregate_sales_data(
        df: pd.DataFrame, 
        group_by: List[str], 
        agg_functions: Dict[str, str] = None
    ) -> pd.DataFrame:
        """Agregar dados de vendas"""
        
        if agg_functions is None:
            agg_functions = {
                'total_price': 'sum',
                'quantity': 'sum',
                'unit_price': 'mean'
            }
        
        # Filtrar apenas colunas que existem
        valid_agg_functions = {
            col: func for col, func in agg_functions.items() 
            if col in df.columns
        }
        
        if not valid_agg_functions:
            raise ValueError("Nenhuma coluna válida para agregação encontrada")
        
        # Agregar dados
        result = df.groupby(group_by).agg(valid_agg_functions).reset_index()
        
        # Calcular métricas adicionais
        if 'total_price' in result.columns and len(group_by) == 1:
            total_revenue = result['total_price'].sum()
            result['market_share_pct'] = (result['total_price'] / total_revenue * 100).round(2)
        
        return result

class TimeSeriesProcessor:
    """Processamento específico para séries temporais"""
    
    @staticmethod
    def create_time_series(
        df: pd.DataFrame, 
        date_column: str, 
        value_column: str,
        freq: str = 'D'
    ) -> pd.DataFrame:
        """Criar série temporal com frequência específica"""
        
        if date_column not in df.columns or value_column not in df.columns:
            raise ValueError("Colunas especificadas não encontradas no DataFrame")
        
        # Converter data
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Criar série temporal
        ts = df.groupby(df[date_column].dt.floor(freq))[value_column].sum()
        
        # Reindexar para incluir todos os períodos
        full_range = pd.date_range(
            start=ts.index.min(), 
            end=ts.index.max(), 
            freq=freq
        )
        
        ts = ts.reindex(full_range, fill_value=0)
        
        return pd.DataFrame({'date': ts.index, 'value': ts.values})
    
    @staticmethod
    def calculate_moving_averages(
        df: pd.DataFrame, 
        value_column: str, 
        windows: List[int] = [7, 30]
    ) -> pd.DataFrame:
        """Calcular médias móveis"""
        
        result = df.copy()
        
        for window in windows:
            ma_column = f'ma_{window}'
            result[ma_column] = result[value_column].rolling(window=window).mean()
        
        return result
    
    @staticmethod
    def detect_trends(
        df: pd.DataFrame, 
        value_column: str, 
        window: int = 30
    ) -> pd.DataFrame:
        """Detectar tendências na série temporal"""
        
        result = df.copy()
        
        # Calcular média móvel
        result['ma'] = result[value_column].rolling(window=window).mean()
        
        # Detectar tendência
        result['trend'] = 'stable'
        result['trend_strength'] = 0.0
        
        for i in range(window, len(result)):
            current_ma = result['ma'].iloc[i]
            previous_ma = result['ma'].iloc[i-window//2] if i >= window//2 else result['ma'].iloc[0]
            
            if pd.notna(current_ma) and pd.notna(previous_ma):
                change_pct = ((current_ma - previous_ma) / previous_ma) * 100
                
                result.loc[i, 'trend_strength'] = abs(change_pct)
                
                if change_pct > 5:
                    result.loc[i, 'trend'] = 'up'
                elif change_pct < -5:
                    result.loc[i, 'trend'] = 'down'
        
        return result
    
    @staticmethod
    def seasonal_decomposition(
        df: pd.DataFrame, 
        value_column: str, 
        period: int = 30
    ) -> Dict[str, pd.Series]:
        """Decomposição sazonal simplificada"""
        
        data = df[value_column].copy()
        
        # Tendência (média móvel)
        trend = data.rolling(window=period, center=True).mean()
        
        # Remover tendência
        detrended = data - trend
        
        # Componente sazonal (média por posição no ciclo)
        seasonal = pd.Series(index=data.index)
        for i in range(len(data)):
            season_pos = i % period
            seasonal.iloc[i] = detrended[detrended.index % period == season_pos].mean()
        
        # Resíduo
        residual = data - trend - seasonal
        
        return {
            'original': data,
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual
        }

class TextProcessor:
    """Processamento de dados de texto"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Limpeza básica de texto"""
        
        if pd.isna(text):
            return ""
        
        # Converter para string
        text = str(text)
        
        # Remover caracteres especiais desnecessários
        text = re.sub(r'[^\w\s\-\.\,\(\)]', '', text)
        
        # Múltiplos espaços para um
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def standardize_product_names(names: List[str]) -> List[str]:
        """Padronizar nomes de produtos"""
        
        standardized = []
        
        for name in names:
            if pd.isna(name):
                standardized.append("")
                continue
            
            # Limpeza básica
            clean_name = TextProcessor.clean_text(name)
            
            # Capitalização
            clean_name = clean_name.title()
            
            # Padronizações específicas
            replacements = {
                'Mg': 'mg',
                'Ml': 'ml',
                'G ': 'g ',
                ' G': 'g',
                'Comprimido': 'comp',
                'Comprimidos': 'comp',
                'Capsula': 'cáps',
                'Cápsula': 'cáps'
            }
            
            for old, new in replacements.items():
                clean_name = clean_name.replace(old, new)
            
            standardized.append(clean_name)
        
        return standardized
    
    @staticmethod
    def extract_dosage(product_name: str) -> Optional[str]:
        """Extrair dosagem do nome do produto"""
        
        if pd.isna(product_name):
            return None
        
        # Padrões comuns de dosagem
        dosage_patterns = [
            r'(\d+\.?\d*\s*mg)',
            r'(\d+\.?\d*\s*ml)',
            r'(\d+\.?\d*\s*g)',
            r'(\d+\.?\d*\s*mcg)',
            r'(\d+\.?\d*\s*ui)',
        ]
        
        for pattern in dosage_patterns:
            match = re.search(pattern, product_name.lower())
            if match:
                return match.group(1)
        
        return None

class ValidationProcessor:
    """Validações de dados"""
    
    @staticmethod
    def validate_sales_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar um registro de venda"""
        
        errors = []
        
        # Campos obrigatórios
        required_fields = ['product_name', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in record or record[field] is None:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validações específicas
        if 'quantity' in record:
            try:
                qty = float(record['quantity'])
                if qty <= 0:
                    errors.append("Quantidade deve ser maior que zero")
            except (ValueError, TypeError):
                errors.append("Quantidade deve ser um número válido")
        
        if 'unit_price' in record:
            try:
                price = float(record['unit_price'])
                if price <= 0:
                    errors.append("Preço unitário deve ser maior que zero")
            except (ValueError, TypeError):
                errors.append("Preço unitário deve ser um número válido")
        
        if 'sale_date' in record and record['sale_date']:
            try:
                sale_date = pd.to_datetime(record['sale_date'])
                if sale_date > datetime.now():
                    errors.append("Data de venda não pode ser futura")
            except:
                errors.append("Data de venda inválida")
        
        # Validar email se presente
        if 'email' in record and record['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            if not re.match(email_pattern, record['email']):
                errors.append("Email inválido")
        
        return len(errors) == 0, errors

class MathUtils:
    """Utilitários matemáticos"""
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Divisão segura evitando divisão por zero"""
        try:
            if denominator == 0:
                return default
            return numerator / denominator
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """Calcular mudança percentual"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def round_currency(value: float) -> float:
        """Arredondar valor monetário"""
        if pd.isna(value):
            return 0.0
        
        decimal_value = Decimal(str(value))
        return float(decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    @staticmethod
    def calculate_compound_growth_rate(
        start_value: float, 
        end_value: float, 
        periods: int
    ) -> float:
        """Calcular taxa de crescimento composto"""
        if start_value <= 0 or end_value <= 0 or periods <= 0:
            return 0.0
        
        return (pow(end_value / start_value, 1 / periods) - 1) * 100

class ExportUtils:
    """Utilitários para exportação"""
    
    @staticmethod
    def prepare_for_excel_export(df: pd.DataFrame) -> pd.DataFrame:
        """Preparar DataFrame para exportação Excel"""
        
        result = df.copy()
        
        # Converter datetime para string formatada
        for col in result.columns:
            if result[col].dtype == 'datetime64[ns]':
                result[col] = result[col].dt.strftime('%d/%m/%Y')
        
        # Arredondar valores numéricos
        for col in result.columns:
            if result[col].dtype in ['float64', 'float32']:
                result[col] = result[col].round(2)
        
        # Substituir NaN por string vazia
        result = result.fillna('')
        
        return result
    
    @staticmethod
    def format_currency_columns(df: pd.DataFrame, currency_columns: List[str]) -> pd.DataFrame:
        """Formatar colunas de moeda"""
        
        result = df.copy()
        
        for col in currency_columns:
            if col in result.columns:
                result[col] = result[col].apply(
                    lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00"
                )
        
        return result

class CacheUtils:
    """Utilitários para cache"""
    
    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """Gerar chave de cache baseada em argumentos"""
        
        key_parts = []
        
        # Adicionar argumentos posicionais
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            elif isinstance(arg, (date, datetime)):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Adicionar argumentos nomeados
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float)):
                key_parts.append(f"{k}:{v}")
            elif isinstance(v, (date, datetime)):
                key_parts.append(f"{k}:{v.isoformat()}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        
        return "_".join(key_parts)
    
    @staticmethod
    def is_cache_valid(cache_timestamp: datetime, ttl_minutes: int = 60) -> bool:
        """Verificar se cache ainda é válido"""
        
        if not cache_timestamp:
            return False
        
        expiry_time = cache_timestamp + timedelta(minutes=ttl_minutes)
        return datetime.now() < expiry_time

# Funções de conveniência
def quick_clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza rápida de dados de vendas"""
    result = DataProcessor.clean_sales_data(df)
    return result.data

def calculate_growth_metrics(
    current_value: float, 
    previous_value: float
) -> Dict[str, float]:
    """Calcular métricas de crescimento"""
    
    return {
        "absolute_change": current_value - previous_value,
        "percentage_change": MathUtils.calculate_percentage_change(previous_value, current_value),
        "growth_factor": MathUtils.safe_divide(current_value, previous_value, 1.0)
    }

def format_analytics_response(
    data: Any, 
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Formatar resposta padrão de analytics"""
    
    return {
        "success": True,
        "data": data,
        "metadata": metadata or {},
        "generated_at": datetime.now().isoformat(),
        "version": "2.0.0"
    }