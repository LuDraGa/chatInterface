import { useState, useRef, useEffect } from "react"
import { useForm, Controller } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { atom, useRecoilState } from "recoil"
import { Info, Folder, FileIcon } from "lucide-react"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

// Recoil state for form data
const formDataState = atom({
  key: 'formDataState',
  default: {}
})

// TODO: Need file selection window for the datastore example
export default function DynamicForm(){
	config = props.config
  const [formData, setFormData] = useRecoilState(formDataState)
  const [dialogOpen, setDialogOpen] = useState(false) // Add state for dialog
  const { register, handleSubmit, control, formState: { errors } } = useForm()

  const getPlacementClass = (placement) => {
    const classes = {
      left: "justify-start",
      right: "justify-end",
      center: "justify-center",
      full: "w-full",
      inline: "inline-flex"
    }
    return classes[placement] || ""
  }

  const renderTooltip = (component, tooltip) => {
    if (!tooltip) return component
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-2">
              {component}
              <Info className="h-4 w-4" />
            </div>
          </TooltipTrigger>
          <TooltipContent>{tooltip}</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  const renderField = (field) => {
    const baseClass = `mb-4 ${getPlacementClass(field.placement)}`
    const fieldName = field.name || field.title.toLowerCase().replace(/\s+/g, '_')

    switch (field.type) {
      case "text":
      case "int":
        return (
          <div className={baseClass}>
            <Label>{field.title}</Label>
            {renderTooltip(
              <Input
                type={field.dataType === "int" ? "number" : "text"}
                placeholder={field.placeholder}
                {...register(fieldName, {
                  required: field.required,
                  valueAsNumber: field.dataType === "int"
                })}
              />,
              field.tooltip
            )}
          </div>
        )

      case "switch":
        return (
          <div className={`flex items-center gap-2 ${baseClass}`}>
            <Label>{field.title}</Label>
            {renderTooltip(
              <Switch
                defaultChecked={field.defaultChecked}
                {...register(fieldName)}
              />,
              field.tooltip
            )}
          </div>
        )

      case "checkbox":
        return (
          <div className={`flex items-center gap-2 ${baseClass}`}>
            <Label>{field.title}</Label>
            {renderTooltip(
              <Checkbox
                defaultChecked={field.defaultChecked}
                {...register(fieldName)}
              />,
              field.tooltip
            )}
          </div>
        )

      case "select":
        return (
          <div className={baseClass}>
            <Label>{field.title}</Label>
            {renderTooltip(
              <Select defaultValue={field.default} onValueChange={(value) => register(fieldName).onChange({ target: { value } })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select..." />
                </SelectTrigger>
                <SelectContent>
                  {field.options?.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>,
              field.tooltip
            )}
          </div>
        )

      case "textarea":
        return (
          <div className={baseClass}>
            <Label>{field.title}</Label>
            {renderTooltip(
              <Textarea
                placeholder={field.placeholder}
                rows={field.rows || 3}
                {...register(fieldName)}
              />,
              field.tooltip
            )}
          </div>
        )

      case "files_input":
			return (
				<div className={baseClass} id={`${fieldName}_files_input`}>
					<Controller
						control={control}  // provided by useForm()
						name={fieldName+"_files"}
						defaultValue={[]}
						render={({ field: { onChange, onBlur, value, ref } }) => (
							<FileInputComponent
								value={value}
								onChange={onChange}
								onBlur={onBlur}
								ref={ref}
							/>
						)}
					/>
				</div>
			);
			
			case "dialog":
        return (
          <div className={baseClass}>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">{field.title}</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>{field.dialog.title}</DialogTitle>
                  {field.dialog.description && (
                    <DialogDescription>{field.dialog.description}</DialogDescription>
                  )}
                </DialogHeader>
                <div className="space-y-4">
                  {field.dialog.fields?.map((dialogField, idx) => (
                    <div key={idx}>{renderField(dialogField)}</div>
                  ))}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        )

      default:
        return null
    }
  }

	useEffect(() => {
		try {		
			console.log("Form data")
			console.log(formData)
			if (Object.keys(formData).length > 0 && formData.datastore_input_files?.length) {
				callAction({name: "create_rag_datastore", payload: formData}).then((res) => {
					if (res.success) {
						toast.success("Datastore created successfully!")
						const data = res.response
						console.log(data)
					} else {
						toast.error("Error creating datastore")
					}
				}).catch((error) => {
					toast.error("Error submitting form backend")
				})
			}
		} catch (error) {
			toast.error("Error submitting form on ui itself")
		}
		
	}, [formData])


	function fileToBase64(file) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(reader.result);
			reader.onerror = error => reject(error);
			reader.readAsDataURL(file); // or readAsArrayBuffer(file) for binary data
		});
	}

  const onSubmit = async (data) => {
		if (data && Object.entries(data).length > 0) {
			const files = data["datastore_input_files"] ?? []; // Your file array
			const serializedFiles = await Promise.all(files.map(async (file) => {
				return {name: file.name, content: await fileToBase64(file)}
			}));
			data["datastore_input_files"] = serializedFiles
			setFormData(data)
		}
		else {
			toast.error("No data to submit")
		}
  }

  return (
		<>
		{/* <form onSubmit={handleSubmit(onSubmit)} className="space-y-4"> */}
      {config && config.map((field, index) => (
        <div key={index}>
          {renderField(field)}
        </div>
      ))}
      <Button type="submit" onClick={handleSubmit(onSubmit)} className="w-full">Submit</Button>
    {/* </form> */}
		</>
  )
}


function FileInputComponent({ value = [], onChange, onBlur }) {
  const [selectedItems, setSelectedItems] = useState(value ?? []);
  const [excludedPatterns, setExcludedPatterns] = useState([]);
  const [error, setError] = useState(null);
  const [regexInput, setRegexInput] = useState('');
  const [expandedDirs, setExpandedDirs] = useState(new Set());

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
		const updatedItems = [...selectedItems, ...files];
    setSelectedItems(updatedItems);
  };
	
	useEffect(() => {
		console.log("Selected items")
    if (onChange) {
			console.log("Selected items")
			const validFiles = getValidFiles()
      onChange(validFiles);
    }
    // Optionally, call onBlur when focus leaves the component
    // if (onBlur) onBlur();
  }, [selectedItems, excludedPatterns]);

  const addExclusionPattern = () => {
    try {
      new RegExp(regexInput); // Validate regex
      setExcludedPatterns((prevPatterns) => [...prevPatterns, regexInput]);
      setRegexInput('');
      setError(null);
    } catch (err) {
      setError('Invalid regular expression');
    }
  };

  const getValidFiles = () => {
    // Filter out excluded files and those matching excluded patterns
    const validFiles = selectedItems.filter(file => {
      // Check if file matches any excludsed pattern
      const matchesPattern = excludedPatterns.some(pattern => {
        try {
          const regex = new RegExp(pattern);
          return regex.test(file.name);
        } catch {
          // If regex is invalid, skip this pattern
          return false;
        }
      });

      // Return true only if file is not excluded and doesn't match patterns
      return !matchesPattern;
    });
		return validFiles;
	}

  const buildFileTree = (files) => {
    const tree = {};
    files.forEach(file => {
      const path = file.webkitRelativePath || file.name;
      const parts = path.split('/');
      let current = tree;
      
      if (parts.length === 1) {
        // Single file
        if (!current.files) current.files = [];
        current.files.push(file);
      } else {
        // File in directory
        for (let i = 0; i < parts.length - 1; i++) {
          const part = parts[i];
          if (!current[part]) {
            current[part] = {};
          }
          current = current[part];
        }
        if (!current.files) current.files = [];
        current.files.push(file);
      }
    });
    return tree;
  };

  const toggleDir = (path) => {
    setExpandedDirs(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const removeDir = (path) => {
    setSelectedItems(prev => prev.filter(item => {
      const itemPath = item.webkitRelativePath || item.name;
      return !itemPath.startsWith(path);
    }));
  };

  const renderFileTree = (tree, path = '') => {
    return (
      <div className="pl-4">
        {Object.entries(tree).map(([key, value]) => {
          if (key === 'files') {
            return value.map((file, index) => (
              <div key={file.name} className="flex items-center pl-8 py-1">
                <FileIcon className="h-4 w-4" />
                <span>{file.name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSelectedItem(selectedItems.indexOf(file))}
									className="ml-auto mr-2" 
                >
                  Remove
                </Button>
              </div>
            ));
          }

          const fullPath = path ? `${path}/${key}` : key;
          const isExpanded = expandedDirs.has(fullPath);

          return (
            <div key={key} className="py-1">
              <div className="flex items-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleDir(fullPath)}
                >
                  {isExpanded ? '▼' : '▶'}
                </Button>
                <Folder className="h-4 w-4" />
                <span>{key}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeDir(fullPath)}
                  className="ml-auto mr-2" 
                >
                  Remove
                </Button>
              </div>
              {isExpanded && renderFileTree(value, fullPath)}
            </div>
          );
        })}
      </div>
    );
  };

  const removeSelectedItem = (index) => {
    setSelectedItems((prevItems) => prevItems.filter((_, i) => i !== index));
  };

  return (
    <div>
      <div>
        <div className="flex flex-col gap-4 p-4 border rounded-lg">
          <div className="flex gap-4">
            <div>
              <Label htmlFor="file-input">Select Files</Label>
              <Input
                id="file-input"
                type="file" 
                multiple
                onChange={handleFileChange}
                className="mt-2"
              />
            </div>
            
            <div>
              <Label htmlFor="dir-input">Select Directory</Label>
              <Input
                id="dir-input"
                type="file"
                webkitdirectory="true"
                multiple
                onChange={handleFileChange} 
                className="mt-2"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="exclusion-pattern">Exclusion Pattern (Regex)</Label>
            <div className="flex gap-2">
              <Input
                id="exclusion-pattern"
                type="text"
                value={regexInput}
                onChange={(e) => setRegexInput(e.target.value)}
                placeholder="e.g. \.git|node_modules"
                className="flex-1"
              />
              <Button onClick={addExclusionPattern}>Add Pattern</Button>
            </div>
          </div>

          <div>
            <Label>Current Exclusion Patterns</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {excludedPatterns.map((pattern, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-gray-100 rounded">
                  <code>{pattern}</code>
                  <Button
                    variant="ghost" 
                    size="sm"
                    onClick={() => setExcludedPatterns(patterns => patterns.filter((_, i) => i !== index))}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Label>Selected Files</Label>
            <div className="mt-2 max-h-60 overflow-y-auto border rounded-md p-2">
              {getValidFiles().length > 0 ? (
                renderFileTree(buildFileTree(getValidFiles()))
              ) : (
                <div className="text-gray-500 text-center py-4">
                  No files selected
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
