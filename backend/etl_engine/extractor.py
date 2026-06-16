import os
import pandas as pd
import logging
from .base import BaseETLComponent

logger = logging.getLogger('etl')


def _read_csv_with_fallback(file_path, encoding=None, sep=None):
    encodings = [encoding] if encoding else ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    separators = [sep] if sep else [';', ',', '\t', None]
    last_err = None
    for enc in encodings:
        for sep_candidate in separators:
            kwargs = {'encoding': enc, 'low_memory': False}
            if sep_candidate is not None:
                kwargs['sep'] = sep_candidate
            try:
                return pd.read_csv(file_path, **kwargs)
            except (UnicodeDecodeError, UnicodeError) as e:
                last_err = e
                continue
            except pd.errors.ParserError:
                continue
            except Exception:
                if sep_candidate is not None:
                    continue
                raise
    raise last_err or Exception("No se pudo leer el archivo CSV con ninguna codificación")


class Extractor(BaseETLComponent):
    def extract(self, file_path, source_type='excel', encoding=None):
        self.log('info', f"Iniciando extracción: {file_path}", 'EXTRACT')
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in ['.xlsx', '.xls'] or source_type == 'excel':
                df = pd.read_excel(file_path, engine='openpyxl' if ext == '.xlsx' else 'xlrd')
            elif ext == '.csv' or source_type == 'csv':
                df = _read_csv_with_fallback(file_path, encoding)
            elif ext == '.json':
                df = pd.read_json(file_path)
            elif ext == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                df = _read_csv_with_fallback(file_path, encoding)

            self.log('info', f"Extraídas {len(df)} filas, {len(df.columns)} columnas", 'EXTRACT')
            return df
        except Exception as e:
            self.log('error', f"Error en extracción: {str(e)}", 'EXTRACT')
            raise

    def extract_from_uploaded(self, uploaded_file):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        df = self.extract(tmp_path)
        os.unlink(tmp_path)
        return df
