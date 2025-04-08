import tkinter as tk
from tkinter import messagebox
import json
import os
import re
from collections import OrderedDict

class DataToolApp:
    def __init__(self, master):
        self.master = master
        master.title("对话数据整理工具 v2.0")
        
        # 界面布局
        self.data_frame = tk.Frame(master)
        self.data_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        self.data_label = tk.Label(self.data_frame, text="对话数据（每行用 | 分隔字段，支持 instruction|input|output 格式）")
        self.data_label.pack(anchor="w")
        
        self.data_text = tk.Text(self.data_frame, height=10)
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # 格式模板部分
        self.format_frame = tk.Frame(master)
        self.format_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        self.format_label = tk.Label(self.format_frame, text="JSON格式模板（已固定为最新结构）")
        self.format_label.pack(anchor="w")
        
        # 固定模板不可编辑
        self.format_text = tk.Text(self.format_frame, height=5, state=tk.DISABLED)
        self.format_text.pack(fill=tk.BOTH, expand=True)
        
        # 预置模板
        fixed_template = '''{
  "instruction": "%instruction%",
  "input": "%input%",
  "output": "%output%"
}'''
        self.format_text.configure(state=tk.NORMAL)
        self.format_text.delete(1.0, tk.END)
        self.format_text.insert(tk.END, fixed_template)
        self.format_text.configure(state=tk.DISABLED)
        
        # 操作按钮
        self.btn_frame = tk.Frame(master)
        self.btn_frame.pack(pady=10)
        
        self.generate_btn = tk.Button(
            self.btn_frame, 
            text="生成JSON", 
            command=self.process_data,
            bg="#4CAF50",
            fg="white",
            width=15
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)

        self.reverse_btn = tk.Button(
            self.btn_frame, 
            text="逆转换到TXT", 
            command=self.reverse_conversion,
            bg="#2196F3",
            fg="white",
            width=15
        )
        self.reverse_btn.pack(side=tk.LEFT, padx=5)

    def process_data(self):
        """处理数据生成JSON"""
        input_data = self.data_text.get("1.0", tk.END).strip()
        if not input_data:
            messagebox.showwarning("输入错误", "请输入对话数据")
            return

        new_entries = []
        required_fields = 3  # instruction|input|output 格式
        
        for line_num, line in enumerate(input_data.split('\n'), 1):
            line = line.strip()
            if not line:
                continue

            # 支持两种分隔符
            if "||" in line:  # 逆转换后的格式
                parts = line.split('||', 1)
                if len(parts) != 2:
                    self.show_line_error(line_num, "请使用 || 分隔问题和回答")
                    return
                instruction_input = parts[0].strip()
                output = parts[1].strip()
                
                # 拆分 instruction 和 input
                if "|" in instruction_input:
                    instruction, input_part = instruction_input.split('|', 1)
                else:
                    instruction = instruction_input
                    input_part = ""
                    
                parts = [
                    instruction.strip(),
                    input_part.strip(),
                    output.strip()
                ]
            else:  # 原始 | 分隔格式
                parts = line.split('|')
                if len(parts) != required_fields:
                    self.show_line_error(line_num, f"需要 {required_fields} 个字段，实际 {len(parts)} 个")
                    return
                parts = [p.strip() for p in parts]

            try:
                entry = OrderedDict([
                    ("instruction", parts[0]),
                    ("input", parts[1]),
                    ("output", parts[2])
                ])
                new_entries.append(entry)
            except Exception as e:
                self.show_line_error(line_num, f"数据转换失败：{str(e)}")
                return

        try:
            self.save_to_json(new_entries)
            messagebox.showinfo("操作成功", 
                f"新增 {len(new_entries)} 条数据\n保存路径：{os.path.abspath('dialogue_data.json')}")
        except Exception as e:
            messagebox.showerror("保存错误", f"文件保存失败：{str(e)}")

    def reverse_conversion(self):
        """将JSON转换回TXT格式"""
        filename = "dialogue_data.json"
        output_file = "dialogue_data.txt"
        
        if not os.path.exists(filename):
            messagebox.showerror("文件不存在", f"未找到 {filename}")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            txt_lines = []
            for idx, entry in enumerate(data, 1):
                try:
                    # 字段验证
                    if "output" not in entry:
                        raise ValueError("缺少必填字段 output")
                    
                    # 获取字段值（带类型转换）
                    instruction = str(entry.get("instruction", "")).strip()
                    user_input = str(entry.get("input", "")).strip()
                    output = str(entry["output"]).strip()
                    
                    # 构建用户输入部分
                    if user_input:
                        user_part = f"{instruction}|{user_input}" if instruction else user_input
                    else:
                        user_part = instruction
                    
                    # 有效性检查
                    if not user_part:
                        raise ValueError("instruction 和 input 不能同时为空")
                    if not output:
                        raise ValueError("output 不能为空")
                        
                    txt_lines.append(f"{user_part}||{output}")
                    
                except Exception as e:
                    error_info = [
                        f"第 {idx} 条数据错误：{str(e)}",
                        "问题数据：",
                        json.dumps(entry, indent=2, ensure_ascii=False)
                    ]
                    messagebox.showerror("数据错误", "\n".join(error_info))
                    return
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(txt_lines))
                
            messagebox.showinfo("转换成功",
                f"生成 {len(txt_lines)} 条数据\n保存路径：{os.path.abspath(output_file)}")
            
        except json.JSONDecodeError:
            messagebox.showerror("格式错误", "JSON文件解析失败，请检查文件内容")
        except Exception as e:
            messagebox.showerror("系统错误", f"未知错误：{str(e)}")

    # 辅助方法
    def show_line_error(self, line_num, message):
        error_msg = f"第 {line_num} 行数据错误：\n{message}"
        messagebox.showerror("数据格式错误", error_msg)

    def save_to_json(self, new_data):
        """保存数据（带去重功能）"""
        filename = "dialogue_data.json"
        existing_data = []
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        # 使用OrderedDict保持顺序
        existing_entries = [OrderedDict(entry) for entry in existing_data]
        new_entries = [OrderedDict(entry) for entry in new_data]
        
        # 去重逻辑
        existing_set = {json.dumps(d, sort_keys=True) for d in existing_entries}
        unique_new = [
            d for d in new_entries
            if json.dumps(d, sort_keys=True) not in existing_set
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_entries + unique_new, f, 
                     indent=2, ensure_ascii=False, sort_keys=False)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("680x720")
    app = DataToolApp(root)
    root.mainloop()