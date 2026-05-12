'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FileText, Database, CreditCard, BarChart3, Menu, X, Search } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const navItems = [
    { href: '/', label: 'Process Invoice', icon: FileText },
    { href: '/query', label: 'Invoice Query', icon: Search },
    { href: '/database', label: 'PO Database', icon: Database },
    { href: '/payments', label: 'Payment History', icon: CreditCard },
  ]

  const isActive = (href: string) => pathname === href

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="fixed top-4 left-4 z-40 md:hidden">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsOpen(!isOpen)}
          className="bg-slate-800 border-slate-700 hover:bg-slate-700"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
      </div>

      {/* Sidebar */}
      <aside className={`
        fixed left-0 top-0 h-screen w-64 bg-slate-800 text-slate-100 border-r border-slate-700
        transform transition-transform duration-300 z-30
        md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        md:static md:w-64
      `}>
        <div className="p-6 border-b border-slate-700">
          <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <span>AP Cortex</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">The Intelligence Layer for Accounts Payable</p>
        </div>

        <nav className="space-y-1 px-4 py-6">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium
                  ${active
                    ? 'bg-primary-500/10 text-primary-400 border border-primary-500/30 shadow-lg'
                    : 'text-slate-300 hover:text-slate-100 hover:bg-slate-700/50'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <p className="text-xs text-slate-500 text-center">
            © 2024 Invoice AI. All rights reserved.
          </p>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}