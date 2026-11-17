import React, { useState, useRef, useEffect, useId } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export interface SelectOption<T = string | number> {
  value: T;
  label: React.ReactNode;
  secondaryLabel?: React.ReactNode;
  badge?: string;
  disabled?: boolean;
}

export interface CustomSelectProps<T = string | number> {
  id?: string;
  name?: string;
  value: T;
  onChange: (value: T) => void;
  options?: SelectOption<T>[];
  children?: React.ReactNode;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  style?: React.CSSProperties;
  size?: 'default' | 'small';
}

export function CustomSelect<T extends string | number = string | number>({
  id,
  name,
  value,
  onChange,
  options: propOptions,
  children,
  placeholder = 'Select an option...',
  disabled = false,
  required = false,
  className = '',
  style,
  size = 'default',
}: CustomSelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const generatedId = useId();
  const selectId = id || generatedId;

  // Derive options from propOptions or children (<option value="...">label</option>)
  const parsedOptions: SelectOption<T>[] = React.useMemo(() => {
    if (propOptions && propOptions.length > 0) {
      return propOptions;
    }

    if (children) {
      const opts: SelectOption<T>[] = [];
      React.Children.forEach(children, (child) => {
        if (React.isValidElement(child) && child.props) {
          const childProps = child.props as any;
          opts.push({
            value: childProps.value as T,
            label: childProps.children,
            disabled: !!childProps.disabled,
          });
        }
      });
      return opts;
    }

    return [];
  }, [propOptions, children]);

  // Find currently selected option
  const selectedOption = parsedOptions.find(
    (opt) => String(opt.value) === String(value)
  );

  // Open / Close toggle handler
  const handleToggle = () => {
    if (disabled) return;
    setIsOpen((prev) => {
      const next = !prev;
      if (next) {
        const idx = parsedOptions.findIndex(
          (opt) => String(opt.value) === String(value)
        );
        setHighlightedIndex(idx >= 0 ? idx : 0);
      }
      return next;
    });
  };

  // Close when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isOpen]);

  // Auto scroll highlighted option into view
  useEffect(() => {
    if (isOpen && listboxRef.current && highlightedIndex >= 0) {
      const items = listboxRef.current.querySelectorAll('li');
      const item = items[highlightedIndex];
      if (item) {
        item.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex, isOpen]);

  const handleSelect = (option: SelectOption<T>) => {
    if (option.disabled) return;
    onChange(option.value);
    setIsOpen(false);
    triggerRef.current?.focus();
  };

  const openWithHighlight = (initialIndex?: number) => {
    const idx =
      initialIndex !== undefined
        ? initialIndex
        : parsedOptions.findIndex((opt) => String(opt.value) === String(value));
    setHighlightedIndex(idx >= 0 ? idx : 0);
    setIsOpen(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!isOpen) {
        openWithHighlight();
      } else {
        setHighlightedIndex((prev) =>
          prev < parsedOptions.length - 1 ? prev + 1 : 0
        );
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (!isOpen) {
        openWithHighlight();
      } else {
        setHighlightedIndex((prev) =>
          prev > 0 ? prev - 1 : parsedOptions.length - 1
        );
      }
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!isOpen) {
        openWithHighlight();
      } else if (highlightedIndex >= 0 && parsedOptions[highlightedIndex]) {
        handleSelect(parsedOptions[highlightedIndex]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    } else if (e.key === 'Tab') {
      if (isOpen) {
        setIsOpen(false);
      }
    }
  };

  const isSmall = size === 'small';

  return (
    <div
      ref={containerRef}
      className={`custom-select-container ${className}`}
      style={style}
    >
      {/* Hidden Native Select for Screen Readers, Form Submissions & Automated Test Compatibility */}
      <select
        id={selectId}
        name={name}
        value={String(value)}
        onChange={(e) => {
          const matched = parsedOptions.find(
            (o) => String(o.value) === e.target.value
          );
          if (matched) onChange(matched.value);
        }}
        tabIndex={-1}
        aria-hidden="true"
        required={required}
        disabled={disabled}
        style={{
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: 0,
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          border: 0,
          pointerEvents: 'none',
        }}
      >
        {parsedOptions.map((opt, i) => (
          <option key={`native-${opt.value}-${i}`} value={String(opt.value)}>
            {typeof opt.label === 'string'
              ? opt.label
              : String(opt.value)}
          </option>
        ))}
      </select>

      {/* Themed Trigger Button */}
      <button
        ref={triggerRef}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={`${selectId}-listbox`}
        id={`${selectId}-button`}
        disabled={disabled}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={`custom-select-trigger ${isOpen ? 'open' : ''} ${
          isSmall ? 'custom-select-sm' : ''
        }`}
      >
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 1,
            fontWeight: 500,
          }}
        >
          {selectedOption ? (
            <>
              <span style={{ textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {selectedOption.label}
              </span>
              {selectedOption.badge && (
                <span
                  className="badge badge-neutral"
                  style={{
                    fontSize: '11px',
                    padding: '1px 7px',
                    marginLeft: 'auto',
                    flexShrink: 0,
                  }}
                >
                  {selectedOption.badge}
                </span>
              )}
            </>
          ) : (
            <span style={{ color: 'var(--text-dim)' }}>{placeholder}</span>
          )}
        </span>

        <ChevronDown
          size={isSmall ? 14 : 16}
          style={{
            flexShrink: 0,
            color: isOpen ? 'var(--accent-dark)' : 'var(--text-muted)',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), color 0.18s ease',
          }}
        />
      </button>

      {/* Themed Dropdown Options Popover */}
      {isOpen && (
        <div className="custom-select-popover">
          <ul
            id={`${selectId}-listbox`}
            ref={listboxRef}
            role="listbox"
            tabIndex={-1}
            className="custom-select-list"
          >
            {parsedOptions.length === 0 ? (
              <li
                style={{
                  padding: '12px 14px',
                  color: 'var(--text-muted)',
                  fontSize: '13px',
                  textAlign: 'center',
                }}
              >
                No options available
              </li>
            ) : (
              parsedOptions.map((option, index) => {
                const isSelected = String(option.value) === String(value);
                const isHighlighted = index === highlightedIndex;

                return (
                  <li
                    key={`opt-${option.value}-${index}`}
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => handleSelect(option)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`custom-select-option ${
                      isSelected ? 'selected' : ''
                    } ${isHighlighted && !isSelected ? 'highlighted' : ''}`}
                  >
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '2px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {option.label}
                      </span>
                      {option.secondaryLabel && (
                        <span
                          style={{
                            fontSize: '11px',
                            color: 'var(--text-muted)',
                            fontWeight: 400,
                          }}
                        >
                          {option.secondaryLabel}
                        </span>
                      )}
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        flexShrink: 0,
                      }}
                    >
                      {option.badge && (
                        <span
                          className={`badge ${
                            isSelected ? 'badge-dark' : 'badge-neutral'
                          }`}
                          style={{ fontSize: '10.5px', padding: '1px 6px' }}
                        >
                          {option.badge}
                        </span>
                      )}

                      {isSelected && (
                        <div className="custom-select-check">
                          <Check size={11} strokeWidth={3} />
                        </div>
                      )}
                    </div>
                  </li>
                );
              })
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

export default CustomSelect;
