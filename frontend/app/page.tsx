'use client';

import Link from 'next/link';
import { Plus, FileAudio, CheckCircle, Clock, ArrowRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-blue-600">MOA</h1>
          <Link
            href="/meetings/upload"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            새 회의 업로드
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-600 to-blue-800 text-white py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            회의를 기록하지 않는다.<br />실행을 만든다.
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            MOA는 AI 기반 회의 액션 매니저입니다.<br />
            회의 녹음을 업로드하면 자동으로 요약하고 액션 아이템을 추출합니다.
          </p>
          <Link
            href="/meetings/upload"
            className="inline-flex items-center gap-2 px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            시작하기
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-12">주요 기능</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<FileAudio className="w-8 h-8 text-blue-600" />}
              title="음성 인식"
              description="한국어에 최적화된 AI가 회의 내용을 정확하게 텍스트로 변환합니다."
            />
            <FeatureCard
              icon={<Clock className="w-8 h-8 text-green-600" />}
              title="자동 요약"
              description="긴 회의도 핵심 내용만 추출하여 간결하게 요약합니다."
            />
            <FeatureCard
              icon={<CheckCircle className="w-8 h-8 text-purple-600" />}
              title="액션 추출"
              description="누가, 언제까지, 무엇을 할지 자동으로 파악하여 정리합니다."
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gray-100 dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h3 className="text-2xl font-bold mb-4">지금 바로 시작하세요</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            회의 녹음 파일을 업로드하고 AI의 마법을 경험하세요.
          </p>
          <Link
            href="/meetings"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            회의 목록 보기
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
          <p>© 2025 MOA - Minutes Of Action. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="p-6 rounded-xl border bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
      <div className="mb-4">{icon}</div>
      <h4 className="text-xl font-semibold mb-2">{title}</h4>
      <p className="text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}
