#!/usr/bin/env python3
"""
github-copilotにあるMDファイルのフロントマターのoutput情報を元に、
{{}}の変数を置換して新しいMDファイルを作成するスクリプト
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any


class AgentTemplateProcessor:
    """エージェントテンプレートファイルを処理するクラス"""
    
    def __init__(self, template_dir: Path, output_base_dir: Path):
        """
        Args:
            template_dir: テンプレートファイルが格納されているディレクトリ
            output_base_dir: 出力ファイルの基準ディレクトリ
        """
        self.template_dir = template_dir
        self.output_base_dir = output_base_dir
        
    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        フロントマターをパースする
        
        Args:
            content: ファイル全体の内容
            
        Returns:
            (フロントマター辞書, 本文) のタプル
        """
        # フロントマターのパターン: --- で囲まれた部分
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            return {}, content
        
        frontmatter_str = match.group(1)
        body = match.group(2)
        
        # YAMLとしてパース
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter or {}, body
        except yaml.YAMLError as e:
            print(f"Warning: YAML parse error: {e}")
            return {}, content
    
    def replace_variables(self, content: str, variables: Dict[str, str]) -> str:
        """
        {{variable_name}} 形式の変数を置換する
        
        Args:
            content: 置換対象のコンテンツ
            variables: 変数名と値の辞書
            
        Returns:
            置換後のコンテンツ
        """
        result = content
        for key, value in variables.items():
            pattern = r'\{\{' + re.escape(key) + r'\}\}'
            result = re.sub(pattern, str(value), result)
        return result
    
    def process_template(self, template_file: Path) -> None:
        """
        テンプレートファイルを処理して新しいファイルを作成する
        
        Args:
            template_file: 処理対象のテンプレートファイル
        """
        print(f"Processing: {template_file}")
        
        # ファイルを読み込む
        content = template_file.read_text(encoding='utf-8')
        
        # フロントマターをパース
        frontmatter, body = self.parse_frontmatter(content)
        
        # output情報を取得
        output_info = frontmatter.get('output', {})
        if not output_info:
            print(f"Warning: No output info found in {template_file}")
            return
        
        # 出力ファイル名を取得
        output_filename = output_info.get('file_name')
        if not output_filename:
            print(f"Warning: No file_name in output info for {template_file}")
            return
        
        # 変数を収集（outputの値が優先）
        variables = {}
        
        # まずmetadataから変数を追加
        metadata = frontmatter.get('metadata', {})
        for key, value in metadata.items():
            variables[key] = value
        
        # outputの全フィールドを変数として追加（file_name以外）
        # outputの値がmetadataの値を上書きする
        for key, value in output_info.items():
            if key != 'file_name':
                variables[key] = value
        
        # 本文の変数を置換
        processed_body = self.replace_variables(body, variables)
        
        # 新しいファイルを作成
        output_path = self.output_base_dir / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # フロントマターも含めた完全な内容を書き込む
        full_content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n{processed_body}"
        output_path.write_text(full_content, encoding='utf-8')
        
        print(f"Created: {output_path}")
    
    def process_all(self) -> None:
        """テンプレートディレクトリ内のすべての.mdファイルを処理する"""
        template_files = list(self.template_dir.glob('*.md'))
        
        if not template_files:
            print(f"No template files found in {self.template_dir}")
            return
        
        print(f"Found {len(template_files)} template file(s)")
        
        for template_file in template_files:
            try:
                self.process_template(template_file)
            except Exception as e:
                print(f"Error processing {template_file}: {e}")


def main():
    """メイン処理"""
    # スクリプトの場所を基準にパスを設定
    script_dir = Path(__file__).parent.parent.parent
    template_dir = script_dir / 'github-copilot'
    output_base_dir = script_dir / 'github-copilot'
    
    print(f"Template directory: {template_dir}")
    print(f"Output base directory: {output_base_dir}")
    print()
    
    processor = AgentTemplateProcessor(template_dir, output_base_dir)
    processor.process_all()


if __name__ == '__main__':
    main()