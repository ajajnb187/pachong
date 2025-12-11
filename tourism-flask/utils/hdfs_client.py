"""
HDFS客户端封装
"""
import json
from datetime import datetime
from hdfs import InsecureClient
from pypinyin import lazy_pinyin
from config import Config
from utils.logger import logger

class HDFSClient:
    """HDFS客户端"""
    
    def __init__(self):
        """初始化HDFS客户端"""
        self.config = Config()
        try:
            self.client = InsecureClient(
                self.config.HDFS_URL,
                user=self.config.HDFS_USER
            )
            logger.info(f"HDFS客户端初始化成功: {self.config.HDFS_URL}")
        except Exception as e:
            logger.error(f"HDFS客户端初始化失败: {str(e)}")
            self.client = None
    
    def save_data(self, data_list, task_id, scenic_spot_name, data_source):
        """
        保存数据到HDFS（如果失败则保存到本地文件）
        
        Args:
            data_list: 数据列表
            task_id: 任务ID
            scenic_spot_name: 景区名称
            data_source: 数据来源
            
        Returns:
            str: HDFS文件路径或本地文件路径，失败返回None
        """
        import os
        
        date_str = datetime.now().strftime('%Y%m%d')
        timestamp = datetime.now().strftime('%H%M%S')
        spot_pinyin = self._pinyin_convert(scenic_spot_name)
        
        try:
            # 构造目录路径
            dir_path = f"/tourism/raw/{date_str}"
            
            # 创建目录
            self.client.makedirs(dir_path)
            
            # 构造文件路径
            file_name = f"{data_source}_{spot_pinyin}_{task_id}_{timestamp}.jsonl"
            file_path = f"{dir_path}/{file_name}"
            
            # 将数据转换为JSONL格式
            jsonl_data = '\n'.join([json.dumps(item, ensure_ascii=False) for item in data_list])
            
            # 写入HDFS
            with self.client.write(file_path, encoding='utf-8', overwrite=True) as writer:
                writer.write(jsonl_data)
            
            logger.info(f"数据已保存到HDFS: {file_path}, 共{len(data_list)}条记录")
            return file_path
            
        except Exception as e:
            logger.warning(f"保存到HDFS失败: {str(e)}，尝试保存到本地文件")
            
            # 备份到本地文件
            try:
                local_dir = f"data/raw/{date_str}"
                os.makedirs(local_dir, exist_ok=True)
                
                file_name = f"{data_source}_{spot_pinyin}_{task_id}_{timestamp}.jsonl"
                local_file = f"{local_dir}/{file_name}"
                
                jsonl_data = '\n'.join([json.dumps(item, ensure_ascii=False) for item in data_list])
                
                with open(local_file, 'w', encoding='utf-8') as f:
                    f.write(jsonl_data)
                
                logger.info(f"数据已保存到本地文件: {local_file}, 共{len(data_list)}条记录")
                return local_file
                
            except Exception as local_error:
                logger.error(f"保存到本地文件也失败: {str(local_error)}")
                return None
    
    def read_data(self, hdfs_path):
        """
        从HDFS读取数据
        
        Args:
            hdfs_path: HDFS路径
            
        Returns:
            list: 数据列表
        """
        if not self.client:
            logger.error("HDFS客户端未初始化，无法读取数据")
            return []
        
        try:
            with self.client.read(hdfs_path, encoding='utf-8') as reader:
                content = reader.read()
                
            # 解析JSON Lines
            data_list = []
            for line in content.strip().split('\n'):
                if line:
                    data_list.append(json.loads(line))
            
            logger.info(f"从HDFS读取数据: {hdfs_path}, 共{len(data_list)}条数据")
            return data_list
            
        except Exception as e:
            logger.error(f"从HDFS读取数据失败: {str(e)}")
            return []
    
    def delete_data(self, hdfs_path):
        """
        删除HDFS数据
        
        Args:
            hdfs_path: HDFS路径
            
        Returns:
            bool: 是否成功
        """
        if not self.client:
            logger.error("HDFS客户端未初始化，无法删除数据")
            return False
        
        try:
            self.client.delete(hdfs_path)
            logger.info(f"已删除HDFS数据: {hdfs_path}")
            return True
        except Exception as e:
            logger.error(f"删除HDFS数据失败: {str(e)}")
            return False
    
    def list_files(self, hdfs_dir):
        """
        列出目录下的文件
        
        Args:
            hdfs_dir: HDFS目录路径
            
        Returns:
            list: 文件列表
        """
        if not self.client:
            logger.error("HDFS客户端未初始化")
            return []
        
        try:
            files = self.client.list(hdfs_dir)
            return files
        except Exception as e:
            logger.error(f"列出HDFS目录失败: {str(e)}")
            return []
    
    def _pinyin_convert(self, chinese_text):
        """
        汉字转拼音
        
        Args:
            chinese_text: 中文文本
            
        Returns:
            str: 拼音
        """
        pinyin_list = lazy_pinyin(chinese_text)
        return ''.join(pinyin_list).lower()

# 创建全局HDFS客户端实例
hdfs_client = HDFSClient()
