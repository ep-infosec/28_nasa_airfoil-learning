'''
    Plot predicted data from random airfoils using Graph Neural Networks and Deep Neural Networks 
'''
import os, glob, random, json
import os.path as osp
from labellines import labelLines
import matplotlib.pyplot as plt
from pathlib import Path
import pickle
import pandas as pd
import torch
from performance import performance_predict_dnn, performance_predict_gnn
from MultiLayerLinear import MultiLayerLinear
from gnn_model import GnnModel
import numpy as np

Path('predicted_results').mkdir(parents=True, exist_ok=True)

'''
    Compare the checkpoints found here. 

    Note: 
        I did some rearranging of the files so that they were in separate folders 
'''
# These 2 will be compared
dnn_no_cp = glob.glob('checkpoints_dnn_no_cp' + "/**/*.pt.tar", recursive = True)
gnn_no_cp = glob.glob('checkpoints_gnn_no_cp' + "/**/*.pt.tar", recursive = True)
dnn_no_cp.extend(gnn_no_cp)
compare_no_cp = dnn_no_cp
# These 2 will be compared
dnn_cp = glob.glob('checkpoints_dnn_cp' + "/**/*.pt.tar", recursive = True)
gnn_cp = glob.glob('checkpoints_gnn_cp' + "/**/*.pt.tar", recursive = True)
dnn_cp.extend(gnn_cp)
compare_cp = dnn_cp



def plot_airfoil_performance(predicted_results,folder,airfoil_name,Reynolds,Ncrit, plot_cp:bool):
    """Creates and saves an example plot

    Args:
        predicted_results (List[Dict[str,float]]): List of results generated by main code 
        filename (str): filename to save the results as 
    """    
    plt.rcParams['font.size'] = '14'
    fig = plt.figure(figsize=(8,7),dpi=150,num=1,clear=True)
    ax1 = fig.add_subplot(111) # Airfoil
    ax1.set_title(predicted_results['airfoil_name'])
    ax1.plot(predicted_results['xss'], predicted_results['yss'],'.-',linewidth=2)
    ax1.plot(predicted_results['xps'], predicted_results['yps'],'.-',linewidth=2)
    ax1.set_ylabel('y/c')
    ax1.set_xlabel('x/c')
    ax1.set_xlim([0,1])
    ax1.set_ylim([-0.5,0.5])
    plt.savefig(os.path.join(folder,f'{airfoil_name}.png'),dpi=300)
    
    plt.clf()
    plt.gcf()
    
    fig = plt.figure(figsize=(18,15),dpi=150,num=2,clear=True)
    ax1 = fig.add_subplot(221) # Cl vs. alpha
    ax1.set_title("Cl vs. angle of attack")
    ax2 = fig.add_subplot(222) # Cd vs. alpha    
    ax2.set_title("Cd vs. angle of attack")
    ax3 = fig.add_subplot(223) # Cdp vs. alpha
    ax3.set_title("Cdp vs. angle of attack")
    ax4 = fig.add_subplot(224) # Cm vs. alpha
    ax4.set_title("Cm vs. angle of attack")
    for model_data in predicted_results['models']:
        model_type = model_data['model_info']['type']
        scaler_type = model_data['model_info']['scaler_type']
        if model_type=='dnn':
            layer_size = model_data['model_info']['Layers'][0]
            nlayers = len(model_data['model_info']['Layers'])
            model_name = f'{scaler_type}-MLP-{layer_size}x{nlayers}'
        else:
            hidden_layers = model_data['model_info']['hiddenLayers']
            if hidden_layers:
                layer_size = model_data['model_info']['hiddenLayers'][0]
                nlayers = len(model_data['model_info']['hiddenLayers'])
                model_name = f'{scaler_type}-GNN-{layer_size}x{nlayers}'
            else:
                model_name = f'{scaler_type}-GNN-None'
        
        df = pd.DataFrame(model_data['predicted_polars']).sort_values(by='alpha')
        ax1.plot(df['alpha'],df['Cl'],'-', label=model_name,linewidth=1.1)
        ax2.plot(df['alpha'],df['Cd'],'-', label=model_name,linewidth=1.1)
        ax3.plot(df['alpha'],df['Cdp'],'-', label=model_name,linewidth=1.1)
        ax4.plot(df['alpha'],df['Cm'],'-', label=model_name,linewidth=1.1)
    
    df_actual = pd.DataFrame(predicted_results['actual_polars']).sort_values(by='alpha')
    model_name='xfoil'
    ax1.plot(df_actual['alpha'],df_actual['Cl'],'.-', label=model_name,linewidth=1.1)
    ax2.plot(df_actual['alpha'],df_actual['Cd'],'.-', label=model_name,linewidth=1.1)
    ax3.plot(df_actual['alpha'],df_actual['Cdp'],'.-', label=model_name,linewidth=1.1)
    ax4.plot(df_actual['alpha'],df_actual['Cm'],'.-', label=model_name,linewidth=1.1)
    
    ax1.set_ylabel('Coefficient of Lift (Cl)')
    ax1.set_xlabel('Angle of Attack (alpha)')

    ax2.set_ylabel('Coefficient of Drag (Cd)')
    ax2.set_xlabel('Angle of Attack (alpha)')

    ax3.set_ylabel('Coefficient of Drag zero lift (Cdp)')
    ax3.set_xlabel('Angle of Attack (alpha)')

    ax4.set_ylabel('Coefficient of Moment (Cm)')
    ax4.set_xlabel('Angle of Attack (alpha)')
    labelLines(ax1.get_lines(), zorder=2.5,fontsize=14)
    labelLines(ax2.get_lines(), zorder=2.5,fontsize=14)
    labelLines(ax3.get_lines(), zorder=2.5,fontsize=14)
    labelLines(ax4.get_lines(), zorder=2.5,fontsize=14)

    # ax1.legend(loc="upper left",fontsize=10)
    # ax2.legend(loc="upper left",fontsize=10)
    # ax3.legend(loc="upper left",fontsize=10)
    # ax4.legend(loc="upper left",fontsize=10)
    fig.tight_layout(pad=3.0) 
    if plot_cp:
        plt.savefig(os.path.join(folder,f'{airfoil_name}-Re_{Reynolds}-Ncrit_{Ncrit}_cp_models.png'),dpi=300)
    else:
        plt.savefig(os.path.join(folder,f'{airfoil_name}-Re_{Reynolds}-Ncrit_{Ncrit}.png'),dpi=300)


    # Plot random examples of Cp
    if plot_cp:
        alphas = [p['alpha'] for p in predicted_results['models'][0]['predicted_polars']]
        alpha_selected = random.sample(alphas, 4) # Pick 3 random angle of attacks 
        alpha_selected.sort()
        fig = plt.figure(figsize=(18,15),dpi=150,num=3,clear=True)
        ax1 = fig.add_subplot(221) # alpha 1 
        ax2 = fig.add_subplot(222) # alpha 2
        ax3 = fig.add_subplot(223) # alpha 3
        ax4 = fig.add_subplot(224) # alpha 4
        ax1.set_title(f"{name}: Cp (Re {Reynolds} Ncrit {Ncrit} alpha {alpha_selected[0]})")
        ax2.set_title(f"{name}: Cp (Re {Reynolds} Ncrit {Ncrit} alpha {alpha_selected[1]})")
        ax3.set_title(f"{name}: Cp (Re {Reynolds} Ncrit {Ncrit} alpha {alpha_selected[2]})")
        ax4.set_title(f"{name}: Cp (Re {Reynolds} Ncrit {Ncrit} alpha {alpha_selected[3]})")
        
        for model_data in predicted_results['models']:
            model_type = model_data['model_info']['type']
            if model_type=='dnn':
                layer_size = model_data['model_info']['Layers'][0]
                nlayers = len(model_data['model_info']['Layers'])
                scaler_type = model_data['model_info']['scaler-type']
                model_name = f'{scaler_type}-MLP-{layer_size}x{nlayers}'
            
                polars = pd.DataFrame(model_data['predicted_polars'])
                polar1 = polars[polars['alpha']==alpha_selected[0]]
                polar2 = polars[polars['alpha']==alpha_selected[1]]
                polar3 = polars[polars['alpha']==alpha_selected[2]]
                polar4 = polars[polars['alpha']==alpha_selected[3]]

                x = np.linspace(0,1,len(polar1['Cp_ss'].to_numpy()[0]))
                # Plot the polars 
                ax1.plot(x, polar1['Cp_ss'].to_numpy()[0], label=model_name, linewidth=1.1)
                ax1.plot(x, polar1['Cp_ps'].to_numpy()[0], label=model_name, linewidth=1.1)

                ax2.plot(x, polar2['Cp_ss'].to_numpy()[0], label=model_name, linewidth=1.1)
                ax2.plot(x, polar2['Cp_ps'].to_numpy()[0], label=model_name, linewidth=1.1)

                ax3.plot(x, polar3['Cp_ss'].to_numpy()[0], label=model_name, linewidth=1.1)
                ax3.plot(x, polar3['Cp_ps'].to_numpy()[0], label=model_name, linewidth=1.1)

                ax4.plot(x, polar4['Cp_ss'].to_numpy()[0], label=model_name, linewidth=1.1)
                ax4.plot(x, polar4['Cp_ps'].to_numpy()[0], label=model_name, linewidth=1.1)            

        model_name='xfoil'
        polar1 = df_actual[df_actual['alpha']==alpha_selected[0]]
        polar2 = df_actual[df_actual['alpha']==alpha_selected[1]]
        polar3 = df_actual[df_actual['alpha']==alpha_selected[2]]
        polar4 = df_actual[df_actual['alpha']==alpha_selected[3]]
        x = np.linspace(0,1,len(polar1['Cp_ss'].to_numpy()[0]))

        ax1.plot(x,polar1['Cp_ss'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)
        ax1.plot(x,polar1['Cp_ps'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)
        
        ax2.plot(x,polar2['Cp_ss'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)
        ax2.plot(x,polar2['Cp_ps'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)

        ax3.plot(x,polar3['Cp_ss'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)
        ax3.plot(x,polar3['Cp_ps'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)

        ax4.plot(x,polar4['Cp_ss'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)
        ax4.plot(x,polar4['Cp_ps'].to_numpy()[0],'.-', label=model_name,linewidth=1.1)
        
        labelLines(ax1.get_lines(), zorder=2.5,fontsize=14)
        labelLines(ax2.get_lines(), zorder=2.5,fontsize=14)
        labelLines(ax3.get_lines(), zorder=2.5,fontsize=14)
        labelLines(ax4.get_lines(), zorder=2.5,fontsize=14)
            
        fig.tight_layout(pad=3.0) 
        plt.savefig(os.path.join(folder,f'{airfoil_name}-Re_{Reynolds}-Ncrit_{Ncrit}_Cp.png'),dpi=300)

def get_random_airfoil_data():
    """Retrieves a random airfoil by searching through the JSON 

    Returns:
        [type]: [description]
    """
    # Load a random airfoil 
    all_json = glob.glob('../generate_xfoil/json/*.json')    
    # Plot random data 
    filename = all_json[random.randrange(0, len(all_json), 1)]
    
    with open(filename,'r') as f:
        airfoil = json.load(f)
        
        name = airfoil['name']
        xss = airfoil['xss']        
        yss = airfoil['yss']

        xps = airfoil['xps']
        yps = airfoil['yps']

        polars = pd.DataFrame(airfoil['polars'])
        unique_reynolds = polars['Re'].unique()
        reynolds = unique_reynolds[random.randrange(0, len(unique_reynolds), 1)]
        
        polars = polars[polars['Re'] == reynolds]
        unique_ncrit = polars['Ncrit'].unique()
        ncrit = unique_ncrit[random.randrange(0, len(unique_ncrit), 1)]
        polars = polars[polars['Ncrit'] == ncrit]

    return name,xss,yss,xps,yps,reynolds,ncrit,polars,airfoil


def compare_models(saved_models,name,xss,yss,xps,yps,scalers):
    """[summary]

    Args:
        saved_models (Dict): Dictionary 
        name (str): Name describing the geometry
        xss (np.ndarray): [description]
        yss (np.ndarray): [description]
        xps (np.ndarray): [description]
        yps (np.ndarray): [description]
        scalers ([type]): [description]
    """
    plot_cp = False
    models_to_evaluate = list()
    for filename in saved_models:
        model_data = torch.load(filename)
        train_params = model_data['parameters']
        if "Gnn" in filename:            
            # Load the model_settings used for training into memory            
            linear_layer = MultiLayerLinear(in_channels=train_params['input_size']*train_params['GnnLayers'][1],out_channels=train_params['output_size'],h_sizes=train_params['hiddenLayers'])
            train_params['type']='gnn'
            if 'minmax' in filename:
                train_params['scaler_type']='minmax'                
                train_params['model']=GnnModel(train_params['input_size'],train_params['GnnLayers'],linear_layers=linear_layer)
                train_params['model'].load_state_dict(model_data['state_dict'])
            else:                
                train_params['scaler_type']='standard'
                train_params['model']=GnnModel(train_params['input_size'],train_params['GnnLayers'],linear_layers=linear_layer)
                train_params['model'].load_state_dict(model_data['state_dict'])
        else:
            train_params['type']='dnn'
            if 'minmax' in filename:
                train_params['scaler_type']='minmax'
                train_params['model']=MultiLayerLinear(in_channels=train_params['input_size'],out_channels=train_params['output_size'],h_sizes=train_params['Layers'])                                
                train_params['model'].load_state_dict(model_data['state_dict'])
            else:            
                train_params['scaler_type']='standard'
                train_params['model']=MultiLayerLinear(in_channels=train_params['input_size'],out_channels=train_params['output_size'],h_sizes=train_params['Layers'])
                train_params['model'].load_state_dict(model_data['state_dict'])
        train_params['model_name']=str(train_params['model'])
        train_params['use_cp'] = True if train_params['output_size']>4 else False
        plot_cp = train_params['use_cp']
        models_to_evaluate.append(train_params)

    ''' This code below is used to evaluate all the models, all models predict the polar on a random airfoil '''

    if len(models_to_evaluate)>0:
        predicted_results = {'airfoil_name': name, 'xss':xss, 'yss':yss,'xps':xps,'yps':yps,'models':[]}
        for model_data in models_to_evaluate:
            if model_data['scaler_type'] == 'minmax':
                scaler = scalers['min_max']
                scaler_cp = scalers['min_max_cp']
            else:
                scaler = scalers['standard']
                scaler_cp = scalers['standard_cp']
            
            predicted_results['model'] = {'type':model_data['type'],'scaler_type':model_data['scaler_type']}
            
            results = list()
            actual_results = list()
            for p in range(len(polars)):
                alpha = polars.iloc[p]['alpha']
                Re = polars.iloc[p]['Re']                
                Ncrit = polars.iloc[p]['Ncrit']
                
                if model_data['type'] == 'gnn':
                    Cl, Cd, Cdp, Cm, Cp_ss, Cp_ps = performance_predict_gnn(model_data['model'],xss,yss,xps,yps,alpha,Re,Ncrit,scaler,scaler_cp,model_data['use_cp'])
                else:
                    Cl, Cd, Cdp, Cm, Cp_ss, Cp_ps = performance_predict_dnn(model_data['model'],xss,yss,xps,yps,alpha,Re,Ncrit,scaler,scaler_cp,model_data['use_cp'])

                results.append({'alpha':alpha,'Re':Re,'Ncrit':Ncrit,
                                'Cl':Cl,
                                'Cd':Cd,
                                'Cm':Cm,
                                'Cdp':Cdp,
                                'Cp_ss':Cp_ss,
                                'Cp_ps':Cp_ps})
                                

                actual_results.append({'alpha':alpha,'Re':Re,'Ncrit':Ncrit,
                                    'Cl':polars.iloc[p]['Cl'],
                                    'Cd':polars.iloc[p]['Cd'],
                                    'Cm':polars.iloc[p]['Cm'],
                                    'Cdp':polars.iloc[p]['Cdp'],
                                    'Cp_ss':polars.iloc[p]['Cp_ss'],
                                    'Cp_ps':polars.iloc[p]['Cp_ps']})
            predicted_results['models'].append({'model_info':model_data, 'predicted_polars':results})
        predicted_results['actual_polars'] = actual_results

        '''
            Create a Plot to compare all models, save to png
        '''
        plot_airfoil_performance(predicted_results,'predicted_results',name,Re,Ncrit,plot_cp)
        

if __name__ == "__main__":
    # Pick a random json file
    # Make a folder with the same name as this file. This is where we save al the images    


    # Load the scalers into memory 
    with open(osp.join('../generate_xfoil/','scalers.pickle'),'rb') as f: # min max of individual y and Cp positions
        scalers = pickle.load(f)

    polars= pd.DataFrame()
    while (polars.empty):   # Make sure I get a random airfoil with data
        name,xss,yss,xps,yps,reynolds,ncrit,polars,airfoil = get_random_airfoil_data()

    # Load all the models into memory for later prediction 
    compare_models(compare_no_cp,name,xss,yss,xps,yps,scalers)
    compare_models(compare_cp,name,xss,yss,xps,yps,scalers)


    
  
